# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_tableview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.tableview

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2026 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import mock
import os
import pytest

from PyQt5 import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
import mslib.msui.tableview as tv
from tests.utils import lsec_xml


class Test_TableView:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        # Create an initial flight track.
        initial_waypoints = [ft.Waypoint(flightlevel=0, location="EDMO", comments="take off OP"),
                             ft.Waypoint(48.10, 10.27, 200),
                             ft.Waypoint(52.32, 09.21, 200),
                             ft.Waypoint(52.55, 09.99, 200),
                             ft.Waypoint(flightlevel=0, location="Hamburg", comments="landing HH")]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSUITableViewWindow(model=waypoints_model)
        self.window.show()

        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_tutorial_mode_mirrors_flighttrack_to_ftml(self):
        """
        In tutorial mode the displayed flight track is silently written to a
        fixed FTML, and the file is rewritten when the model changes.
        """
        from mslib.utils import constants
        ftml = os.path.join(constants.MSUI_CONFIG_PATH, "tutorial_flighttrack.ftml")
        if os.path.exists(ftml):
            os.remove(ftml)
        self.window.tutorial_mode = True
        model = self.window.waypoints_model
        # setting the model connects the change signals and writes the file
        self.window.setFlightTrackModel(model)
        assert os.path.exists(ftml)
        content = open(ftml).read()
        assert "<FlightTrack" in content
        assert content.count("<Waypoint") == len(model.waypoints)
        # a model change triggers a rewrite
        os.remove(ftml)
        model.insertRows(0, rows=1, waypoints=[ft.Waypoint(10.0, 20.0, 200)])
        assert os.path.exists(ftml)
        with open(ftml) as f:
            data = f.read()
            assert data.count("<Waypoint") == len(model.waypoints)
            assert '    <Waypoint location="" lat="10.0" lon="20.0" flightlevel="200">' in data.split('\n')

    def test_tutorial_mode_enable_save_writes_initial_ftml(self):
        """
        Views get their model via the constructor (bypassing setFlightTrackModel),
        so the creator calls enable_tutorial_flighttrack_save to write the initial
        FTML and start tracking (mscolab).
        """
        from mslib.utils import constants
        ftml = os.path.join(constants.MSUI_CONFIG_PATH, "tutorial_flighttrack.ftml")
        if os.path.exists(ftml):
            os.remove(ftml)
        self.window.tutorial_mode = True
        self.window.enable_tutorial_flighttrack_save()
        assert os.path.exists(ftml)
        with open(ftml) as f:
            data = f.read()
            assert data.count("<Waypoint") == len(self.window.waypoints_model.waypoints)

    def test_open_hex(self):
        """
        Tests opening the hexagon dock widget.
        """
        self.window.cbTools.currentIndexChanged.emit(1)
        assert len(self.window.docks) == 2
        assert self.window.docks[0] is not None
        assert self.window.docks[1] is None

    def test_open_perf_settings(self):
        """
        Tests opening the performance settings dock widget.
        """
        self.window.cbTools.currentIndexChanged.emit(2)
        assert len(self.window.docks) == 2
        assert self.window.docks[0] is None
        assert self.window.docks[1] is not None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_insertremove_hexagon(self, mockbox):
        """
        Test inserting and removing hexagons in TableView using the Hexagon dockwidget
        """
        self.window.cbTools.currentIndexChanged.emit(1)
        assert len(self.window.waypoints_model.waypoints) == 5
        QtTest.QTest.mouseClick(self.window.docks[0].widget().pbAddHexagon, QtCore.Qt.LeftButton)
        assert len(self.window.waypoints_model.waypoints) == 12
        assert mockbox.call_count == 0
        QtTest.QTest.mouseClick(self.window.docks[0].widget().pbRemoveHexagon, QtCore.Qt.LeftButton)
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 5

    @mock.patch("mslib.msui.performance_settings.get_open_filename",
                return_value=os.path.join(
                    os.path.dirname(__file__), "..", "data", "performance_simple.json"))
    def test_performance(self, mockopen):
        """
        Check effect of performance settings on TableView
        """
        self.window.cbTools.currentIndexChanged.emit(2)

        self.window.waypoints_model.performance_settings = DEFAULT_PERFORMANCE
        self.window.waypoints_model.update_distances(0)
        self.window.waypoints_model.dataChanged.emit(
            self.window.waypoints_model.index(0, 0), self.window.waypoints_model.index(0, 0))
        self.window.resizeColumns()
        assert self.window.waypoints_model.columnCount() == 15
        visible = dict(DEFAULT_PERFORMANCE)
        visible["visible"] = True
        self.window.waypoints_model.performance_settings = visible
        self.window.waypoints_model.update_distances(0)
        self.window.waypoints_model.dataChanged.emit(
            self.window.waypoints_model.index(0, 0), self.window.waypoints_model.index(0, 0))
        self.window.resizeColumns()
        assert self.window.waypoints_model.columnCount() == 15
        # todo this does not check that actually something happens
        QtTest.QTest.mouseClick(self.window.docks[1].widget().pbLoadPerformance, QtCore.Qt.LeftButton)
        assert mockopen.call_count == 1

    def test_show_linear_data(self):
        """
        The "show data" checkbox appends the data columns of the linear view.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        model.set_linear_data_from_xml([lsec_xml(
            lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
            values=("nan", "0.05", "0.06", "0.07", "nan"))])
        # the data is hidden as long as the checkbox is unchecked
        assert model.columnCount() == 15

        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert self.window.cbShowLinearData.isChecked()
        assert model.columnCount() == 16
        column = ft.LINEAR_DATA_COLUMN
        assert model.headerData(
            column, QtCore.Qt.Horizontal).value() == "Mole fraction of ozone (Linear)\n(ppmv)"
        # no values where the aircraft is on the ground
        assert [model.data(model.index(row, column)).value() for row in range(model.rowCount())] == \
            ["", "0.05", "0.06", "0.07", ""]

        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert not self.window.cbShowLinearData.isChecked()
        assert model.columnCount() == 15

    def test_show_linear_data_of_another_flight_track(self):
        """
        Switching to another flight track keeps the "show data" checkbox and
        shows the data columns that the linear view retrieved for that track.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        model.set_linear_data_from_xml([lsec_xml(
            lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
            values=("nan", "0.05", "0.06", "0.07", "nan"))])
        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert model.columnCount() == 16

        # the linear view of the other flight track plots two layers
        other = ft.WaypointsTableModel("other")
        other.insertRows(0, rows=3, waypoints=[ft.Waypoint(48.10, 10.27, 200),
                                               ft.Waypoint(52.32, 9.21, 200),
                                               ft.Waypoint(52.55, 9.99, 200)])
        other_waypoints = other.all_waypoint_data()
        other.set_linear_data_from_xml([
            lsec_xml(title=title, unit="ppmv",
                     lats=[wp.lat for wp in other_waypoints],
                     lons=[wp.lon for wp in other_waypoints],
                     values=values)
            for title, values in (("Ozone", ("0.1", "0.2", "0.3")),
                                  ("Water vapour", ("1", "2", "nan")))])

        self.window.setFlightTrackModel(other)
        assert self.window.cbShowLinearData.isChecked()
        assert other.columnCount() == 17
        column = ft.LINEAR_DATA_COLUMN
        assert [other.headerData(column + i, QtCore.Qt.Horizontal).value() for i in range(2)] == \
            ["Ozone\n(ppmv)", "Water vapour\n(ppmv)"]
        assert [other.data(other.index(row, column)).value() for row in range(other.rowCount())] == \
            ["0.1", "0.2", "0.3"]
        assert [other.data(other.index(row, column + 1)).value() for row in range(other.rowCount())] == \
            ["1", "2", ""]

        # the data of the other flight track is hidden again on demand
        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert other.columnCount() == 15

        # ... and the track shown before does not notify this window any more
        assert model.receivers(model.linearDataChanged) == 0

    def test_show_linear_data_without_linear_view(self):
        """
        The "show data" checkbox is unchecked and greyed out as long as no
        linear view provides data.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        # no linear view has plotted this flight track yet
        assert not self.window.cbShowLinearData.isEnabled()
        assert not self.window.cbShowLinearData.isChecked()

        data = [lsec_xml(lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
                         values=("nan", "0.05", "0.06", "0.07", "nan"))]
        model.set_linear_data_from_xml(data)
        assert self.window.cbShowLinearData.isEnabled()
        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert model.columnCount() == 16

        # closing the linear view drops the data columns and the tick
        model.clear_linear_data()
        assert not self.window.cbShowLinearData.isEnabled()
        assert not self.window.cbShowLinearData.isChecked()
        assert not model.linear_data_visible
        assert model.columnCount() == 15

        # ... the tick and the columns are back with the next plot
        model.set_linear_data_from_xml(data)
        assert self.window.cbShowLinearData.isEnabled()
        assert self.window.cbShowLinearData.isChecked()
        assert model.columnCount() == 16

    def test_show_linear_data_disabled_for_flight_track_without_data(self):
        """
        Switching to a flight track that no linear view plots unchecks and
        greys the "show data" checkbox out.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        model.set_linear_data_from_xml([lsec_xml(
            lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
            values=("nan", "0.05", "0.06", "0.07", "nan"))])
        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert self.window.cbShowLinearData.isEnabled()

        other = ft.WaypointsTableModel("other")
        other.insertRows(0, rows=2, waypoints=[ft.Waypoint(48.10, 10.27, 200),
                                               ft.Waypoint(52.32, 9.21, 200)])
        self.window.setFlightTrackModel(other)
        assert not self.window.cbShowLinearData.isEnabled()
        assert not self.window.cbShowLinearData.isChecked()
        assert not other.linear_data_visible
        assert other.columnCount() == 15

    def test_show_linear_data_of_flight_tracks_switched_back_and_forth(self):
        """
        The data columns follow the active flight track: they are shown as
        soon as the linear view has retrieved the values of that track, also
        when switching back and forth between flight tracks.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        data = [lsec_xml(lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
                         values=("nan", "0.05", "0.06", "0.07", "nan"))]
        model.set_linear_data_from_xml(data)
        QtTest.QTest.mouseClick(self.window.cbShowLinearData, QtCore.Qt.LeftButton)
        assert model.columnCount() == 16

        other = ft.WaypointsTableModel("other")
        other.insertRows(0, rows=2, waypoints=[ft.Waypoint(48.10, 10.27, 200),
                                               ft.Waypoint(52.32, 9.21, 200)])
        other_waypoints = other.all_waypoint_data()
        other_data = [lsec_xml(lats=[wp.lat for wp in other_waypoints],
                               lons=[wp.lon for wp in other_waypoints], values=("0.1", "0.2"))]
        # the linear view drops the values of the track it does not plot any more
        model.clear_linear_data()
        self.window.setFlightTrackModel(other)
        assert not self.window.cbShowLinearData.isEnabled()
        assert not self.window.cbShowLinearData.isChecked()

        # the plot of the new flight track arrives and its data is shown
        other.set_linear_data_from_xml(other_data)
        assert self.window.cbShowLinearData.isEnabled()
        assert self.window.cbShowLinearData.isChecked()
        assert other.columnCount() == 16
        assert [other.data(other.index(row, ft.LINEAR_DATA_COLUMN)).value()
                for row in range(other.rowCount())] == ["0.1", "0.2"]

        # ... and the same when switching back to the first flight track
        other.clear_linear_data()
        self.window.setFlightTrackModel(model)
        assert not self.window.cbShowLinearData.isChecked()
        model.set_linear_data_from_xml(data)
        assert self.window.cbShowLinearData.isChecked()
        assert model.columnCount() == 16
        assert [model.data(model.index(row, ft.LINEAR_DATA_COLUMN)).value()
                for row in range(model.rowCount())] == ["", "0.05", "0.06", "0.07", ""]

    def test_show_linear_data_not_wanted_stays_hidden_on_switch(self):
        """
        Data columns that the user has switched off stay off when the linear
        view provides data for another flight track.
        """
        model = self.window.waypoints_model
        waypoints = model.all_waypoint_data()
        model.set_linear_data_from_xml([lsec_xml(
            lats=[wp.lat for wp in waypoints], lons=[wp.lon for wp in waypoints],
            values=("nan", "0.05", "0.06", "0.07", "nan"))])
        assert not self.window.cbShowLinearData.isChecked()

        other = ft.WaypointsTableModel("other")
        other.insertRows(0, rows=2, waypoints=[ft.Waypoint(48.10, 10.27, 200),
                                               ft.Waypoint(52.32, 9.21, 200)])
        other_waypoints = other.all_waypoint_data()
        self.window.setFlightTrackModel(other)
        other.set_linear_data_from_xml([lsec_xml(
            lats=[wp.lat for wp in other_waypoints], lons=[wp.lon for wp in other_waypoints],
            values=("0.1", "0.2"))])
        assert self.window.cbShowLinearData.isEnabled()
        assert not self.window.cbShowLinearData.isChecked()
        assert other.columnCount() == 15

    def test_insert_point(self):
        """
        Check insertion of points
        """
        item = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(2, 0))
        QtTest.QTest.mouseClick(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item.center())
        assert len(self.window.waypoints_model.waypoints) == 5
        wps = list(self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.btAddWayPointToFlightTrack, QtCore.Qt.LeftButton)
        wps2 = self.window.waypoints_model.waypoints
        assert len(self.window.waypoints_model.waypoints) == 6
        assert all(_x == _y for _x, _y in zip(wps[:3], wps2[:3])), (wps, wps2)
        assert all(_x == _y for _x, _y in zip(wps[3:], wps2[4:])), (wps, wps2)

    def test_clone_point(self):
        """
        Check cloning of points
        """
        item = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(2, 0))
        QtTest.QTest.mouseClick(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item.center())
        assert len(self.window.waypoints_model.waypoints) == 5
        wps = list(self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.btCloneWaypoint, QtCore.Qt.LeftButton)
        wps2 = self.window.waypoints_model.waypoints
        assert len(self.window.waypoints_model.waypoints) == 6
        assert all(_x == _y for _x, _y in zip(wps[:3], wps2[:3])), (wps, wps2)
        assert all(_x == _y for _x, _y in zip(wps[3:], wps2[4:])), (wps, wps2)

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_point(self, mockbox):
        """
        Check insertion of points
        """
        item = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(1, 0))
        QtTest.QTest.mouseClick(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item.center())
        assert len(self.window.waypoints_model.waypoints) == 5
        wps = list(self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.btDeleteWayPoint, QtCore.Qt.LeftButton)
        wps2 = self.window.waypoints_model.waypoints
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 4
        assert all([_x == _y for _x, _y in zip(wps[:1], wps2[:1])])
        assert all([_x == _y for _x, _y in zip(wps[2:], wps2[1:])])

    def test_reverse_points(self):
        """
        Check insertion of points
        """
        wps = list(self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.btInvertDirection, QtCore.Qt.LeftButton)
        wps2 = self.window.waypoints_model.waypoints
        assert all([_x == _y for _x, _y in zip(wps[::-1], wps2)])

    @pytest.mark.skipif(reason="drag/drop does not work on QT5")
    def test_drag_point(self):
        """
        Check insertion of points
        """
        assert len(self.window.waypoints_model.waypoints) == 5
        wps_before = list(self.window.waypoints_model.waypoints)
        item1 = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(2, 0))
        item2 = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(3, 0))
        QtTest.QTest.mousePress(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item1.center())
        QtTest.QTest.mouseMove(
            self.window.tableWayPoints.viewport(),
            item2.center())
        QtTest.QTest.mouseRelease(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item2.center())
        assert len(self.window.waypoints_model.waypoints) == 5
        wps_after = list(self.window.waypoints_model.waypoints)
        assert wps_before != wps_after, (wps_before, wps_after)

    def test_roundtrip(self):
        """
        Test connecting the last and first point
        Test connecting the first point to itself
        """
        count = len(self.window.waypoints_model.waypoints)

        # Test if the last waypoint connects to the first
        self.window.update_roundtrip_enabled()
        assert self.window.is_roundtrip_possible()
        self.window.make_roundtrip()
        assert len(self.window.waypoints_model.waypoints) == count + 1
        first = self.window.waypoints_model.waypoints[0]
        dupe = self.window.waypoints_model.waypoints[-1]
        assert first.lat == dupe.lat and first.lon == dupe.lon

        # Check if roundtrip is disabled if the last and first point are equal
        self.window.update_roundtrip_enabled()
        assert not self.window.is_roundtrip_possible()
        assert not self.window.btRoundtrip.isEnabled()
        self.window.make_roundtrip()
        assert len(self.window.waypoints_model.waypoints) == count + 1

        # Remove connection
        self.window.waypoints_model.removeRows(count, 1)
        assert len(self.window.waypoints_model.waypoints) == count
