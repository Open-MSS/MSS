# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_linearview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.linearview

    This file is part of MSS.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021-2023 by the MSS team, see AUTHORS.
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
import multiprocessing
import tempfile
from mslib.mswms.mswms import application
from PyQt5 import QtWidgets, QtTest, QtCore
from mslib.msui import flighttrack as ft
import mslib.msui.linearview as tv
from mslib.msui.mpl_qtwidget import _DEFAULT_SETTINGS_LINEARVIEW
from tests.utils import wait_until_signal
from conftest import QAPP

PORTS = list(range(26000, 26500))


class Test_MSS_LV_Options_Dialog(object):
    def setup_method(self):
        self.application = QAPP.instance()
        self.window = tv.MSUI_LV_Options_Dialog(settings=_DEFAULT_SETTINGS_LINEARVIEW)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown_method(self):
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


class Test_MSSLinearViewWindow(object):
    def setup_method(self):
        self.application = QAPP.instance()
        initial_waypoints = [ft.Waypoint(40., 25., 300), ft.Waypoint(60., -10., 400), ft.Waypoint(40., 10, 300)]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSUILinearViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown_method(self):
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
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(100, 100), -1)
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.linearview.MSUI_LV_Options_Dialog")
    def test_options(self, mockdlg, mockbox):
        QtTest.QTest.mouseClick(self.window.lvoptionbtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert mockdlg.call_count == 1
        assert mockdlg.return_value.setModal.call_count == 1
        assert mockdlg.return_value.exec_.call_count == 1
        assert mockdlg.return_value.destroy.call_count == 1


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_LinearViewWMS(object):
    def setup_method(self):
        self.application = QAPP.instance()
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
        self.window = tv.MSUILinearViewWindow(model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()
        self.window.cbTools.currentIndexChanged.emit(1)
        QtWidgets.QApplication.processEvents()
        self.wms_control = self.window.docks[0].widget()
        self.wms_control.multilayers.cbWMS_URL.setEditText("")

    def teardown_method(self):
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
        assert mockbox.critical.call_count == 0
