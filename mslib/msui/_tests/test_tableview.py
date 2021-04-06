# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_tableview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.tableview

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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
import pytest
import sys

from PyQt5 import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
import mslib.msui.tableview as tv


class Test_TableView(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        # Create an initital flight track.
        initial_waypoints = [ft.Waypoint(flightlevel=0, location="EDMO", comments="take off OP"),
                             ft.Waypoint(48.10, 10.27, 200),
                             ft.Waypoint(52.32, 09.21, 200),
                             ft.Waypoint(52.55, 09.99, 200),
                             ft.Waypoint(flightlevel=0, location="Hamburg", comments="landing HH")]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSSTableViewWindow(model=waypoints_model)
        self.window.show()

        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_open_hex(self):
        """
        Tests opening the hexagon dock widget.
        """
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_insertremove_hexagon(self, mockbox):
        """
        Test inserting and removing hexagons in TableView using the Hexagon dockwidget
        """
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 5
        QtTest.QTest.mouseClick(self.window.docks[0].widget().pbAddHexagon, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 12
        assert mockbox.call_count == 0
        QtTest.QTest.mouseClick(self.window.docks[0].widget().pbRemoveHexagon, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 5

    def test_performance(self):
        """
        Check effect of performance settings on TableView
        """
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
        QtWidgets.QApplication.processEvents()
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
        QtWidgets.QApplication.processEvents()
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
        QtWidgets.QApplication.processEvents()
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
        QtWidgets.QApplication.processEvents()
        wps2 = self.window.waypoints_model.waypoints
        assert all([_x == _y for _x, _y in zip(wps[::-1], wps2)])

    def test_drag_point(self):
        """
        Check insertion of points
        """

        pytest.skip("drag/drop testing does not seem to work o qt5.")

        assert len(self.window.waypoints_model.waypoints) == 5
        wps_before = list(self.window.waypoints_model.waypoints)
        item1 = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(2, 0))
        item2 = self.window.tableWayPoints.visualRect(
            self.window.waypoints_model.index(3, 0))
        QtTest.QTest.mousePress(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item1.center())
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseMove(
            self.window.tableWayPoints.viewport(),
            item2.center())
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseRelease(
            self.window.tableWayPoints.viewport(),
            QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item2.center())
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 5
        wps_after = list(self.window.waypoints_model.waypoints)
        assert wps_before != wps_after, (wps_before, wps_after)

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_roundtrip(self, mockbox):
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
        assert mockbox.critical.call_count == 0
