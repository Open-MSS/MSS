# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_tableview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.tableview

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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
import sys

from mslib.msui.performance_settings import DEFAULT_PERFORMANCE
from mslib.msui import flighttrack as ft
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest
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
        QtTest.QTest.qWaitForWindowShown(self.window)
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

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
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
        assert self.window.waypoints_model.columnCount() == 13
        visible = dict(DEFAULT_PERFORMANCE)
        visible["visible"] = True
        self.window.waypoints_model.performance_settings = visible
        self.window.waypoints_model.update_distances(0)
        self.window.waypoints_model.dataChanged.emit(
            self.window.waypoints_model.index(0, 0), self.window.waypoints_model.index(0, 0))
        self.window.resizeColumns()
        assert self.window.waypoints_model.columnCount() == 13
        # todo this does not check that actually something happens

    def test_insert_point(self):
        """
        Check insertion of points
        """
        QtTest.QTest.keyClick(self.window.tableWayPoints, QtCore.Qt.Key_Down)
        assert len(self.window.waypoints_model.waypoints) == 5
        wps = list(self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.btAddWayPointToFlightTrack, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wps2 = self.window.waypoints_model.waypoints
        assert len(self.window.waypoints_model.waypoints) == 6
        assert all([_x == _y for _x, _y in zip(wps[:2], wps2[:2])])
        assert all([_x == _y for _x, _y in zip(wps[2:], wps2[3:])])

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_point(self, mockbox):
        """
        Check insertion of points
        """
        QtTest.QTest.keyClick(self.window.tableWayPoints, QtCore.Qt.Key_Down)
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
