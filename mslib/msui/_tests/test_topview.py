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

from __future__ import division

import mock
import os
import shutil
import sys
import paste
import paste.httpserver
import multiprocessing
import tempfile
import mslib.mswms.wms
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
import mslib.msui.topview as tv


class Test_MSS_TV_MapAppearanceDialog(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = tv.MSS_TV_MapAppearanceDialog()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_show(self, mockcrit):
        assert mockcrit.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_get(self, mockcrit):
        assert mockcrit.critical.call_count == 0
        self.window.get_settings()
        assert mockcrit.critical.call_count == 0


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
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_wms(self, mockbox):
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_sat(self, mockbox):
        self.window.cbTools.currentIndexChanged.emit(2)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_rs(self, mockcrit):
        self.window.cbTools.currentIndexChanged.emit(3)
        QtWidgets.QApplication.processEvents()
        rsdock = self.window.docks[2].widget()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(rsdock.cbDrawTangents, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        rsdock.dsbTangentHeight.setValue(6)
        QtWidgets.QApplication.processEvents()
        rsdock.dsbObsAngle.setValue(70)
        QtTest.QTest.mouseClick(rsdock.cbDrawTangents, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        rsdock.cbShowSolarAngle.setChecked(True)
        assert mockcrit.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_open_kml(self, mockbox):
        self.window.cbTools.currentIndexChanged.emit(4)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_insert_point(self, mockbox):
        """
        Test inserting a point inside and outside the canvas
        """
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=QtCore.QPoint(1, 1))
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        # click again on same position
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 5
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.critical")
    def test_remove_point_yes(self, mockcrit, mockbox):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['delete_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockcrit.call_count == 0
        assert len(self.window.waypoints_model.waypoints) == 3
        assert mockbox.call_count == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question",
                return_value=QtWidgets.QMessageBox.No)
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.critical")
    def test_remove_point_no(self, mockcrit, mockbox):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['delete_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mousePress(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseRelease(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()
        assert mockbox.call_count == 1
        assert len(self.window.waypoints_model.waypoints) == 4
        assert mockcrit.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_move_point(self, mockbox):
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        self.window.mpl.navbar._actions['move_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mousePress(self.window.mpl.canvas, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        point = QtCore.QPoint((self.window.width() // 3), self.window.height() // 2)
        QtTest.QTest.mouseMove(
            self.window.mpl.canvas, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseRelease(
            self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 4
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_map_options(self, mockbox):
        self.window.mpl.canvas.map.set_graticule_visible(True)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.mpl.canvas.map.set_graticule_visible(False)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.mpl.canvas.map.set_fillcontinents_visible(False)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.mpl.canvas.map.set_fillcontinents_visible(True)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.mpl.canvas.map.set_coastlines_visible(False)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.mpl.canvas.map.set_coastlines_visible(True)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0


class Test_TopViewWMS(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.thread = multiprocessing.Process(
            target=paste.httpserver.serve,
            args=(mslib.mswms.wms.application,),
            kwargs={"host": "127.0.0.1", "port": "8082", "use_threadpool": False})
        self.thread.start()

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSSTopViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        self.wms_control = self.window.docks[0].widget()
        self.wms_control.cbWMS_URL.setEditText("")

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self.tempdir)
        self.thread.terminate()

    def query_server(self, url):
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClicks(self.wms_control.cbWMS_URL, url)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.wms_control.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_server_getmap(self, mockbox):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server("http://127.0.0.1:8082")
        QtTest.QTest.mouseClick(self.wms_control.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtWidgets.QApplication.processEvents()
        self.window.mpl.canvas.redraw_map()
        assert mockbox.critical.call_count == 0
