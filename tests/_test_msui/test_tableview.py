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

import datetime
import json
import mock
import os
import time
import pytest

from PyQt5 import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
from mslib.msui.aircraft import AIRCRAFT_DUMMY, SimpleAircraft
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
        from mslib.msui.utils import constants
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
        from mslib.msui.utils import constants
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
        model = self.window.waypoints_model
        assert model.columnCount() == 15
        changes = []
        model.performanceDataChanged.connect(lambda: changes.append(1))
        QtTest.QTest.mouseClick(self.window.docks[1].widget().pbLoadPerformance, QtCore.Qt.LeftButton)
        assert mockopen.call_count == 1
        # the aircraft is applied once, not for each weight of the dock
        assert changes == [1]
        assert model.performance_settings["aircraft"] is not DEFAULT_PERFORMANCE["aircraft"]
        # the take off weight of the file, i.e. its fuel
        assert model.waypoints[0].weight == 91000
        assert model.performance_settings["empty_weight"] == 56000
        assert model.performance_settings["fuel"] == model.waypoints[0].rem_fuel == 35000

    @pytest.mark.parametrize("change", [
        {"empty_weight": None}, {"takeoff_weight": None}, {"empty_weight": "56000"},
        {"empty_weight": 95000}, {"empty_weight": -1}, {"takeoff_weight": 1e8, "empty_weight": 0},
        {"climb": [[0, 0]]}, {"cruise": "abc"}, {"descent": [[["a"]]]}, "not readable",
        {"cruise": [[0.0, 0.0, 0.0, 2900.0]]}],
        ids=["no-empty-weight", "no-takeoff-weight", "string", "empty-above-takeoff", "negative", "too-heavy",
             "short-table-row", "table-string", "table-nested", "not-readable", "cannot-compute"])
    def test_performance_with_bad_weights(self, tmp_path, change):
        """
        An aircraft file that can't be read, without proper weights or tables, or that the flight track
        can't be computed with (e.g. no cruise speed) is rejected, as the error message says, not applied.
        """
        with open(os.path.join(os.path.dirname(__file__), "..", "data", "performance_simple.json")) as source:
            performance = json.load(source)
        filename = tmp_path / "performance.json"
        if change == "not readable":
            # a directory can't be opened as a file
            filename.mkdir()
        else:
            for key, value in change.items():
                if value is None:
                    del performance[key]
                else:
                    performance[key] = value
            filename.write_text(json.dumps(performance))
        self.window.cbTools.currentIndexChanged.emit(2)
        model = self.window.waypoints_model
        settings = dict(model.performance_settings)
        with mock.patch("mslib.msui.performance_settings.get_open_filename", return_value=str(filename)), \
                mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critical:
            QtTest.QTest.mouseClick(self.window.docks[1].widget().pbLoadPerformance, QtCore.Qt.LeftButton)
        critical.assert_called_once()
        assert model.performance_settings == settings
        dock = self.window.docks[1].widget()
        assert (dock.lbAircraftName.text(), dock.dsbEmptyWeight.value()) == (
            settings["aircraft"].name, settings["empty_weight"])

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
            ["", 0.05, 0.06, 0.07, ""]

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
            [0.1, 0.2, 0.3]
        assert [other.data(other.index(row, column + 1)).value() for row in range(other.rowCount())] == \
            [1., 2., ""]

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
                for row in range(other.rowCount())] == [0.1, 0.2]

        # ... and the same when switching back to the first flight track
        other.clear_linear_data()
        self.window.setFlightTrackModel(model)
        assert not self.window.cbShowLinearData.isChecked()
        model.set_linear_data_from_xml(data)
        assert self.window.cbShowLinearData.isChecked()
        assert model.columnCount() == 16
        assert [model.data(model.index(row, ft.LINEAR_DATA_COLUMN)).value()
                for row in range(model.rowCount())] == ["", 0.05, 0.06, 0.07, ""]

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

    def _copy_table_to_clipboard_csv(self, locale, delimiter):
        """
        Trigger the copy-to-clipboard button under a fixed QLocale (so the
        test does not depend on the locale of the machine it runs on) and
        return the clipboard content parsed as CSV rows.
        """
        import csv
        import io

        previous_locale = QtCore.QLocale()
        QtCore.QLocale.setDefault(locale)
        try:
            QtWidgets.QApplication.clipboard().clear()
            QtTest.QTest.mouseClick(self.window.btCopyToClipboard, QtCore.Qt.LeftButton)
            text = QtWidgets.QApplication.clipboard().text()
        finally:
            QtCore.QLocale.setDefault(previous_locale)
        assert text
        return list(csv.reader(io.StringIO(text), delimiter=delimiter))

    def test_copy_table_to_clipboard(self):
        """
        Copying the table to the clipboard produces CSV text with the
        columns currently shown, leaving out columns that are empty for
        every waypoint (e.g. data columns of the linear view without data).
        Numbers use the decimal point of the active QLocale ('.' for the
        C locale used here), which also determines the field delimiter.
        """
        rows = self._copy_table_to_clipboard_csv(QtCore.QLocale.c(), delimiter=",")
        header = [cell.strip() for cell in rows[0]]
        expected_header = [" ".join(column[0].split()) for column in ft.TABLE_FULL]
        assert header == expected_header
        assert len(rows) == 1 + len(self.window.waypoints_model.waypoints)
        assert rows[1][0] == "EDMO"
        assert rows[1][-1] == "take off OP"
        assert rows[2][1:3] == ["48.1", "10.27"]
        assert rows[-1][0] == "Hamburg"
        assert rows[-1][-1] == "landing HH"

    def test_copy_table_to_clipboard_uses_locale_decimal_point(self):
        """
        With a locale that uses a comma as decimal point, numbers are
        copied with a comma, and the field delimiter switches to ";" so the
        CSV stays unambiguous to parse (the usual European CSV/Excel
        convention).
        """
        de_locale = QtCore.QLocale(QtCore.QLocale.German, QtCore.QLocale.Germany)
        rows = self._copy_table_to_clipboard_csv(de_locale, delimiter=";")
        assert rows[2][1:3] == ["48,1", "10,27"]

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_edit_time_shifts_flight(self, mocksave):
        """
        Editing the time of one waypoint sets the takeoff time such that the
        waypoint is reached at that time; all other times follow.
        """
        default_takeoff = DEFAULT_PERFORMANCE["takeoff_time"]
        model = self.window.waypoints_model
        assert model.flags(model.index(2, ft.TIME_UTC)) & QtCore.Qt.ItemIsEditable
        legs = [wp.utc_time - model.waypoints[0].utc_time for wp in model.waypoints]
        model.modified = False

        assert model.setData(model.index(2, ft.TIME_UTC), "2030-01-01 12:00:00")
        target = datetime.datetime(2030, 1, 1, 12)
        # QDateTime holds milliseconds only
        ms = datetime.timedelta(milliseconds=1)
        assert abs(model.waypoints[2].utc_time - target) < ms
        assert model.data(model.index(2, ft.TIME_UTC)).value() == "2030-01-01 12:00:00"
        takeoff = model.performance_settings["takeoff_time"].toPyDateTime()
        assert abs(takeoff - (target - legs[2])) < ms
        assert all(abs((wp.utc_time - takeoff) - leg) < ms for wp, leg in zip(model.waypoints, legs))
        assert DEFAULT_PERFORMANCE["takeoff_time"] is default_takeoff

        # a time edit is no change of the flight plan
        assert not model.modified
        # unparsable input is discarded
        assert not model.setData(model.index(2, ft.TIME_UTC), "noon")
        assert model.data(model.index(2, ft.TIME_UTC)).value() == "2030-01-01 12:00:00"

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_edit_time_with_editor(self, mocksave):
        model = self.window.waypoints_model
        index = model.index(3, ft.TIME_UTC)
        delegate = self.window.tableWayPoints.itemDelegate()
        editor = delegate.createEditor(self.window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
        assert isinstance(editor, QtWidgets.QDateTimeEdit)
        delegate.setEditorData(editor, index)
        assert editor.dateTime().toString("yyyy-MM-dd HH:mm:ss") == model.data(index).value()
        target = QtCore.QDateTime(2031, 6, 15, 8, 30, 0)
        target.setTimeSpec(QtCore.Qt.UTC)
        editor.setDateTime(target)
        delegate.setModelData(editor, model, index)
        assert model.data(index).value() == "2031-06-15 08:30:00"

    def test_pick_location_changes_once(self):
        """
        Picking a location sets its coordinates and name, a single change of the flight track.
        """
        model = self.window.waypoints_model
        index = model.index(1, ft.LOCATION)
        changes = []
        model.dataChanged.connect(lambda *args: changes.append(args))
        delegate = self.window.tableWayPoints.itemDelegate()
        editor = delegate.createEditor(self.window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
        editor.setCurrentText("Hamburg")
        delegate.setModelData(editor, model, index)
        assert len(changes) == 1
        assert (model.waypoints[1].location, model.waypoints[1].lat, model.waypoints[1].lon) == ("Hamburg", 53.55, 9.99)

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_unchanged_editor_keeps_time(self, mocksave):
        """
        The editor shows full seconds; committing it unchanged must not shift
        the flight by the rounding difference.
        """
        model = self.window.waypoints_model
        model.setData(model.index(1, ft.TIME_UTC), "2030-01-01 12:00:00")
        index = model.index(3, ft.TIME_UTC)
        assert model.waypoints[3].utc_time.microsecond != 0
        takeoff = model.performance_settings["takeoff_time"]
        changes = []
        model.performanceDataChanged.connect(lambda: changes.append(1))
        delegate = self.window.tableWayPoints.itemDelegate()
        editor = delegate.createEditor(self.window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
        delegate.setEditorData(editor, index)
        delegate.setModelData(editor, model, index)
        assert model.performance_settings["takeoff_time"] == takeoff
        assert changes == []

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_performance_dock_keeps_edited_time(self, mocksave):
        model = self.window.waypoints_model
        self.window.cbTools.currentIndexChanged.emit(2)
        model.setData(model.index(1, ft.TIME_UTC), "2030-01-01 12:00:00")
        changes = []
        model.performanceDataChanged.connect(lambda: changes.append(1))
        fuel = model.performance_settings["fuel"]
        spinbox = self.window.docks[1].widget().dsbEmptyWeight
        spinbox.selectAll()
        QtTest.QTest.keyClicks(spinbox, "60000")
        assert changes == []
        QtTest.QTest.keyClick(spinbox, QtCore.Qt.Key_Return)
        # the flight track is updated once, not for each key stroke
        assert changes == [1]
        assert model.performance_settings["empty_weight"] == 60000
        # the fuel stays, the aircraft is heavier
        assert model.performance_settings["fuel"] == fuel
        assert model.waypoints[0].weight == 60000 + fuel
        assert model.data(model.index(1, ft.TIME_UTC)).value() == "2030-01-01 12:00:00"

    @pytest.mark.skipif(not hasattr(time, "tzset"), reason="time.tzset is available on Unix only")
    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_edit_time_in_local_dst_gap(self, mocksave, monkeypatch):
        """
        Times are UTC throughout; a time that does not exist in the local
        time zone (daylight saving gap) must still round trip through the editor.
        """
        monkeypatch.setenv("TZ", "Europe/Berlin")
        time.tzset()
        try:
            model = self.window.waypoints_model
            index = model.index(1, ft.TIME_UTC)
            assert model.setData(index, "2030-03-31 02:30:00")
            assert model.data(index).value() == "2030-03-31 02:30:00"
            delegate = self.window.tableWayPoints.itemDelegate()
            editor = delegate.createEditor(self.window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
            delegate.setEditorData(editor, index)
            assert editor.dateTime().toString("yyyy-MM-dd HH:mm:ss") == "2030-03-31 02:30:00"
            delegate.setModelData(editor, model, index)
            assert model.data(index).value() == "2030-03-31 02:30:00"
        finally:
            monkeypatch.undo()
            time.tzset()

    def _edit(self, row, column, text=None, enter=False):
        """Opens the editor of a cell, sets text if given, confirms it with Enter if asked, and leaves the cell."""
        model = self.window.waypoints_model
        index = model.index(row, column)
        delegate = self.window.tableWayPoints.itemDelegate()
        editor = delegate.createEditor(self.window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
        delegate.setEditorData(editor, index)
        if text is not None:
            if isinstance(editor, QtWidgets.QComboBox):
                editor.setCurrentText(text)
            else:
                editor.setText(text)
        if enter:
            QtTest.QTest.keyClick(editor, QtCore.Qt.Key_Return)
        delegate.setModelData(editor, model, index)

    def test_unchanged_location_of_unnamed_waypoint(self):
        model = self.window.waypoints_model
        before = (model.waypoints[1].location, model.waypoints[1].lat, model.waypoints[1].lon)
        changes = []
        model.dataChanged.connect(lambda *args: changes.append(args))
        self._edit(1, ft.LOCATION)
        after = (model.waypoints[1].location, model.waypoints[1].lat, model.waypoints[1].lon)
        assert after == before == ("", 48.10, 10.27)
        assert changes == []

    @pytest.mark.parametrize("column", [ft.LAT, ft.LON, ft.FLIGHTLEVEL, ft.PRESSURE, ft.LOCATION])
    def test_unchanged_commit_changes_nothing(self, column):
        """
        The table shows rounded values; leaving the editor unchanged must not move the waypoint or drop its name.
        """
        model = self.window.waypoints_model
        model.setData(model.index(1, ft.LAT), 48.1234)
        model.setData(model.index(1, ft.LOCATION), "custom")
        before = vars(model.waypoints[1]).copy()
        changes = []
        model.dataChanged.connect(lambda *args: changes.append(args))
        self._edit(1, column)
        assert vars(model.waypoints[1]) == before
        assert changes == []

    def test_clear_name(self):
        """
        No name is just no name, not the position of another waypoint without a name.
        """
        model = self.window.waypoints_model
        before = (model.waypoints[4].lat, model.waypoints[4].lon)
        self._edit(4, ft.LOCATION, "")
        assert (model.waypoints[4].location, model.waypoints[4].lat, model.waypoints[4].lon) == ("",) + before

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_performance_dock_follows_the_flight_track(self, mocksave):
        self.window.cbTools.currentIndexChanged.emit(2)
        dock = self.window.docks[1].widget()
        other = ft.WaypointsTableModel("other", waypoints=[ft.Waypoint(1., 1., 0), ft.Waypoint(2., 2., 0)])
        other.performance_settings = dict(other.performance_settings, empty_weight=40000, fuel=10000,
                                          aircraft=SimpleAircraft(dict(AIRCRAFT_DUMMY, name="OTHER")))
        self.window.setFlightTrackModel(other)
        assert dock.lbAircraftName.text() == "OTHER"
        assert dock.dsbEmptyWeight.value() == 40000
        dock.dsbEmptyWeight.setValue(45000)
        assert other.performance_settings["aircraft"].name == "OTHER"
        assert (other.performance_settings["empty_weight"], other.performance_settings["fuel"]) == (45000, 10000)

    def test_pick_name_of_another_waypoint(self):
        model = self.window.waypoints_model
        model.setData(model.index(2, ft.LOCATION), "custom")
        changes = []
        model.dataChanged.connect(lambda *args: changes.append(args))
        self._edit(1, ft.LOCATION, "custom")
        # one change, with the name
        assert len(changes) == 1
        assert (model.waypoints[1].location, model.waypoints[1].lat, model.waypoints[1].lon) == ("custom", 52.32, 9.21)

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_edit_takeoff_fuel(self, mocksave):
        model = self.window.waypoints_model
        assert model.flags(model.index(0, ft.REM_FUEL)) & QtCore.Qt.ItemIsEditable
        assert not model.flags(model.index(1, ft.REM_FUEL)) & QtCore.Qt.ItemIsEditable
        assert not model.setData(model.index(1, ft.REM_FUEL), "1000")
        changes, flight_plan_changes = [], []
        model.performanceDataChanged.connect(lambda: changes.append(1))
        model.dataChanged.connect(lambda *args: flight_plan_changes.append(args))
        self._edit(0, ft.REM_FUEL)
        assert changes == []
        self._edit(0, ft.REM_FUEL, "20000")
        assert changes == [1]
        assert flight_plan_changes == []
        assert model.performance_settings["fuel"] == model.waypoints[0].rem_fuel == 20000
        assert model.waypoints[0].weight == model.performance_settings["empty_weight"] + 20000
        assert mocksave.call_args[0][1]["fuel"] == 20000
        assert not model.setData(model.index(0, ft.REM_FUEL), "-1")
        assert model.performance_settings["fuel"] == 20000

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_takeoff_time_limits(self, mocksave):
        """
        A time whose waypoint times can't be computed is rejected before it is stored.
        """
        model = self.window.waypoints_model
        assert model.setData(model.index(0, ft.TIME_UTC), "8999-12-31 23:59:00")
        takeoff = model.performance_settings["takeoff_time"]
        saved = mocksave.call_count
        assert not model.setData(model.index(0, ft.TIME_UTC), "9999-12-31 23:00:00")
        assert not model.setData(model.index(0, ft.TIME_UTC), "1899-12-31 23:00:00")
        assert model.performance_settings["takeoff_time"] == takeoff
        assert mocksave.call_count == saved
        # an unchanged commit of a later waypoint, near the limit, doesn't shift the flight
        assert model.waypoints[3].utc_time.year == 9000
        self._edit(3, ft.TIME_UTC)
        assert model.performance_settings["takeoff_time"] == takeoff

    def test_takeoff_time_out_of_range_is_reset_at_load(self):
        broken = QtCore.QDateTime(QtCore.QDate(9999, 12, 31), QtCore.QTime(23, 0), QtCore.Qt.UTC)
        stored = dict(DEFAULT_PERFORMANCE, takeoff_time=broken)
        with mock.patch("mslib.msui.flighttrack.load_settings_qsettings", return_value=stored):
            model = ft.WaypointsTableModel("", waypoints=[ft.Waypoint(0., 0., 0.), ft.Waypoint(10., 10., 300.)])
        assert model.performance_settings["takeoff_time"] == DEFAULT_PERFORMANCE["takeoff_time"]

    def test_model_connections(self):
        """
        The window listens to the flight track it shows, once.
        """
        first = self.window.waypoints_model
        other = ft.WaypointsTableModel("other", waypoints=[ft.Waypoint(1., 1., 0)])
        self.window.setFlightTrackModel(other)
        self.window.setFlightTrackModel(other)
        with mock.patch.object(self.window, "is_roundtrip_possible", return_value=True) as possible:
            other.insertRows(1, waypoints=[ft.Waypoint(2., 2., 0)])
            assert possible.call_count == 1
            first.insertRows(1, waypoints=[ft.Waypoint(2., 2., 0)])
            assert possible.call_count == 1

    def test_seconds_rounded(self):
        assert ft.seconds_to_string(3599.5) == "01:00:00"
        assert ft.seconds_to_string(3599.4) == "00:59:59"
        assert ft.format_utc_time(datetime.datetime(2030, 1, 1, 11, 59, 59, 500000)) == "2030-01-01 12:00:00"

    def test_repick_location(self):
        """
        Picking a waypoint's name again moves it to the first waypoint of that name, as on develop.
        """
        model = self.window.waypoints_model
        model.replace_waypoints([ft.Waypoint(50., 6., 0), ft.Waypoint(52., 8., 250, location="Turn"),
                                 ft.Waypoint(53., 10., 250, location="Turn"), ft.Waypoint(51., 12., 0)])
        # only passing through the cell keeps the waypoint, also a moved one
        self._edit(2, ft.LOCATION)
        assert (model.waypoints[2].lat, model.waypoints[2].lon) == (53., 10.)
        self._edit(2, ft.LOCATION, "Turn", enter=True)
        assert (model.waypoints[2].lat, model.waypoints[2].lon) == (52., 8.)
        # the first one stays where it is
        self._edit(1, ft.LOCATION, "Turn", enter=True)
        assert (model.waypoints[1].lat, model.waypoints[1].lon) == (52., 8.)

    def test_repick_configured_location(self):
        """
        Picking a configured location again moves a waypoint of that name back to it.
        """
        model = self.window.waypoints_model
        self._edit(1, ft.LOCATION, "Hamburg")
        model.waypoints[1].lat = 53.  # e.g. from a flight track file; moving it drops the name
        self._edit(1, ft.LOCATION)
        assert (model.waypoints[1].location, model.waypoints[1].lat) == ("Hamburg", 53.)
        self._edit(1, ft.LOCATION, enter=True)
        assert (model.waypoints[1].location, model.waypoints[1].lat, model.waypoints[1].lon) == ("Hamburg", 53.55, 9.99)

    @mock.patch("mslib.msui.flighttrack.save_settings_qsettings")
    def test_columns_follow_fuel(self, mocksave):
        """
        A fuel edit changes no flight plan, still a larger fuel may need wider columns.
        """
        with mock.patch.object(self.window, "resizeColumns") as resize:
            self._edit(0, ft.REM_FUEL, "9999999")
        resize.assert_called()


class Test_TableViewsOfOneFlightTrack:
    """
    Several table views with performance settings show one flight track: whatever is changed in
    one of them, all show the performance settings of the flight track (#3315 review).
    """

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, tmp_path):
        self.model = ft.WaypointsTableModel("", waypoints=[
            ft.Waypoint(50., 6., 0), ft.Waypoint(52., 8., 250), ft.Waypoint(51., 12., 0)])
        self.windows = [tv.MSUITableViewWindow(model=self.model) for _ in range(3)]
        for window in self.windows:
            window.cbTools.currentIndexChanged.emit(2)
        performance = dict(AIRCRAFT_DUMMY, name="OTHER", takeoff_weight=80000, empty_weight=50000)
        self.filename = tmp_path / "other.json"
        self.filename.write_text(json.dumps(performance))
        with mock.patch("mslib.msui.flighttrack.save_settings_qsettings"):
            yield
        for window in self.windows:
            window.hide()

    def docks(self):
        return [window.docks[1].widget() for window in self.windows]

    def check(self):
        settings = self.model.performance_settings
        for dock in self.docks():
            assert dock.lbAircraftName.text() == settings["aircraft"].name
            assert dock.dsbEmptyWeight.value() == settings["empty_weight"]
        assert self.model.waypoints[0].rem_fuel == settings["fuel"]
        assert self.model.waypoints[0].weight == settings["empty_weight"] + settings["fuel"]

    def load(self, dock):
        with mock.patch("mslib.msui.performance_settings.get_open_filename", return_value=str(self.filename)):
            QtTest.QTest.mouseClick(dock.pbLoadPerformance, QtCore.Qt.LeftButton)

    @pytest.mark.parametrize("loading, editing", [(0, 1), (1, 0), (2, 2)])
    def test_load_in_one_edit_in_another(self, loading, editing):
        """
        Reimar's case: load an aircraft in one view, change the empty weight in another.
        """
        self.check()
        self.load(self.docks()[loading])
        assert self.model.performance_settings["aircraft"].name == "OTHER"
        assert (self.model.performance_settings["empty_weight"], self.model.performance_settings["fuel"]) == \
            (50000, 30000)
        self.check()
        self.docks()[editing].dsbEmptyWeight.setValue(52000)
        assert self.model.performance_settings["aircraft"].name == "OTHER"
        assert (self.model.performance_settings["empty_weight"], self.model.performance_settings["fuel"]) == \
            (52000, 30000)
        self.check()

    def test_edits_in_any_view(self):
        windows, docks = self.windows, self.docks()
        self.load(docks[0])
        for window, dock in zip(windows, docks):
            dock.dsbEmptyWeight.setValue(dock.dsbEmptyWeight.value() + 1000)
            self.check()
            delegate = window.tableWayPoints.itemDelegate()
            index = self.model.index(0, ft.REM_FUEL)
            editor = delegate.createEditor(window.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
            delegate.setEditorData(editor, index)
            editor.setText(str(self.model.performance_settings["fuel"] + 500))
            delegate.setModelData(editor, self.model, index)
            self.check()
        assert self.model.performance_settings["aircraft"].name == "OTHER"
        assert (self.model.performance_settings["empty_weight"], self.model.performance_settings["fuel"]) == \
            (53000, 31500)

    def test_view_opened_later(self):
        self.load(self.docks()[0])
        window = tv.MSUITableViewWindow(model=self.model)
        window.cbTools.currentIndexChanged.emit(2)
        self.windows.append(window)
        self.check()


def test_performance_dock_keeps_typed_text_with_a_fractional_weight(qtbot):
    """
    The box shows whole numbers: a stored weight with decimals, e.g. from older settings, was always taken as
    changed, and showing the settings again replaced the text being typed (#3364 review)
    """
    from mslib.msui.performance_settings import MSUI_PerformanceSettingsWidget
    settings = dict(DEFAULT_PERFORMANCE, empty_weight=55000.4)
    dock = MSUI_PerformanceSettingsWidget(settings_dict=settings)
    qtbot.addWidget(dock)
    dock.show()
    dock.dsbEmptyWeight.setFocus()
    dock.dsbEmptyWeight.selectAll()
    QtTest.QTest.keyClicks(dock.dsbEmptyWeight, "60000")
    dock.show_settings(settings)
    assert dock.dsbEmptyWeight.text() == "60000"
