# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_topview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.topview

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
import pytest
import sys
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
from mslib._tests.utils import close_modal_messagebox
import mslib.msui.topview as tv


class Test_MSSTopViewWindow(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSSTopViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_open_wms(self):
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)

    def test_open_sat(self):
        self.window.cbTools.currentIndexChanged.emit(2)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)

    def test_open_rs(self):
        self.window.cbTools.currentIndexChanged.emit(3)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)

    def test_open_kml(self):
        self.window.cbTools.currentIndexChanged.emit(4)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)

    def test_insert_point(self):
        """
        Test inserting a point inside and outside the canvas
        """
        QtTest.QTest.mouseClick(self.window.btInsWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=QtCore.QPoint(1, 1))
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        assert not close_modal_messagebox(self.window)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_point_yes(self, mockbox):
        QtTest.QTest.mouseClick(self.window.btInsWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.btDelWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 3
        assert not close_modal_messagebox(self.window)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.No)
    def test_remove_point_no(self, mockbox):
        QtTest.QTest.mouseClick(self.window.btInsWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.btDelWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 4
        assert not close_modal_messagebox(self.window)

    def test_move_point(self):
        pytest.skip("not finished")
        QtTest.QTest.mouseClick(self.window.btInsWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.btMvWaypoint, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mousePress(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # QtTest.QTest.mouseMove(self.window.mpl.canvas, pos=QtCore.QPoint(100, 100))
        # QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseRelease(
            self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=QtCore.QPoint(100, 100))
        self.application.exec_()
        assert len(self.window.waypoints_model.waypoints) == 4
        assert False

    def test_map_options(self):
        self.window.mpl.canvas.map.set_graticule_visible(True)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        self.window.mpl.canvas.map.set_graticule_visible(False)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        self.window.mpl.canvas.map.set_fillcontinents_visible(False)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        self.window.mpl.canvas.map.set_fillcontinents_visible(True)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        self.window.mpl.canvas.map.set_coastlines_visible(False)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        self.window.mpl.canvas.map.set_coastlines_visible(True)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
