# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_sideview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.sideview

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
import os
import pytest
import shutil
import sys
import multiprocessing
import tempfile
from mslib.mswms.mswms import application
from PyQt5 import QtWidgets, QtTest, QtCore, QtGui
from mslib.msui import flighttrack as ft
import mslib.msui.sideview as tv
from mslib._tests.utils import wait_until_signal

PORTS = list(range(19000, 19500))


class Test_MSS_SV_OptionsDialog(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = tv.MSS_SV_OptionsDialog()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_show(self, mockcrit):
        assert mockcrit.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_get(self, mockcrit):
        self.window.get_settings()
        assert mockcrit.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_addLevel(self, mockcrit):
        QtTest.QTest.mouseClick(self.window.btAdd, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockcrit.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_removeLevel(self, mockcrit):
        QtTest.QTest.mouseClick(self.window.btDelete, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockcrit.critical.call_count == 0

    def test_getFlightLevels(self):
        levels = self.window.get_flight_levels()
        assert all(x == y for x, y in zip(levels, [300, 320, 340]))
        QtTest.QTest.mouseClick(self.window.btAdd, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        levels = self.window.get_flight_levels()
        assert all(x == y for x, y in zip(levels, [0, 300, 320, 340]))

    @mock.patch("PyQt5.QtWidgets.QColorDialog.getColor", return_value=QtGui.QColor())
    def test_setColour(self, mockdlg):
        QtTest.QTest.mouseClick(self.window.btFillColour, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockdlg.call_count == 1


class Test_MSSSideViewWindow(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        initial_waypoints = [ft.Waypoint(40., 25., 300), ft.Waypoint(60., -10., 400), ft.Waypoint(40., 10, 300)]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSSSideViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_wms(self, mockbox):
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_mouse_over(self, mockbox):
        # Test mouse over
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(782, 266), -1)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(20, 20), -1)
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.sideview.MSS_SV_OptionsDialog")
    def test_options(self, mockdlg, mockbox):
        QtTest.QTest.mouseClick(self.window.btOptions, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert mockdlg.call_count == 1
        assert mockdlg.return_value.setModal.call_count == 1
        assert mockdlg.return_value.exec_.call_count == 1
        assert mockdlg.return_value.destroy.call_count == 1

    @pytest.mark.skip("fails with mockbox.critical.call_count in reverse order")
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_insert_point(self, mockbox):
        """
        Test inserting a point inside and outside the canvas
        """
        self.window.mpl.navbar._actions['insert_wp'].trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.waypoints_model.waypoints) == 3
        point = self.window.mpl.canvas.rect().center()
        QtTest.QTest.mouseClick(self.window.mpl.canvas, QtCore.Qt.LeftButton, pos=point)
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

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_y_axes(self, mockbox):
        self.window.getView().get_settings()["secondary_axis"] = "pressure altitude"
        self.window.getView().set_settings(self.window.getView().get_settings())
        self.window.getView().get_settings()["secondary_axis"] = "flight level"
        self.window.getView().set_settings(self.window.getView().get_settings())
        assert mockbox.critical.call_count == 0


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_SideViewWMS(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.port = PORTS.pop()
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.thread = multiprocessing.Process(
            target=application.run,
            args=("127.0.0.1", self.port))
        self.thread.start()

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSSSideViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        self.wms_control = self.window.docks[0].widget()
        self.wms_control.multilayers.cbWMS_URL.setEditText("")

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self.tempdir)
        self.thread.terminate()

    def query_server(self, url):
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClicks(self.wms_control.multilayers.cbWMS_URL, url)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.wms_control.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.wms_control.cpdlg.canceled)

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_server_getmap(self, mockbox):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        QtTest.QTest.mouseClick(self.wms_control.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.wms_control.image_displayed)
        assert self.window.getView().image is not None
        self.window.getView().clear_figure()
        assert self.window.getView().image is None
        assert mockbox.critical.call_count == 0
