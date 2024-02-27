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
import tempfile
from PyQt5 import QtTest, QtCore
from mslib.msui import flighttrack as ft
import mslib.msui.linearview as tv
from mslib.msui.mpl_qtwidget import _DEFAULT_SETTINGS_LINEARVIEW


class Test_MSS_LV_Options_Dialog:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.window = tv.MSUI_LV_Options_Dialog(settings=_DEFAULT_SETTINGS_LINEARVIEW)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_show(self):
        pass

    def test_get(self):
        self.window.get_settings()


class Test_MSSLinearViewWindow:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        initial_waypoints = [ft.Waypoint(40., 25., 300), ft.Waypoint(60., -10., 400), ft.Waypoint(40., 10, 300)]

        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)

        self.window = tv.MSUILinearViewWindow(model=waypoints_model)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_open_wms(self):
        self.window.cbTools.currentIndexChanged.emit(1)

    def test_mouse_over(self):
        # Test mouse over
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(782, 266), -1)
        QtTest.QTest.mouseMove(self.window.mpl.canvas, QtCore.QPoint(100, 100), -1)

    @mock.patch("mslib.msui.linearview.MSUI_LV_Options_Dialog")
    def test_options(self, mockdlg):
        QtTest.QTest.mouseClick(self.window.lvoptionbtn, QtCore.Qt.LeftButton)
        assert mockdlg.call_count == 1
        assert mockdlg.return_value.setModal.call_count == 1
        assert mockdlg.return_value.exec_.call_count == 1
        assert mockdlg.return_value.destroy.call_count == 1


class Test_LinearViewWMS:
    @pytest.fixture(autouse=True)
    def setup(self, qapp, mswms_server):
        self.url = mswms_server
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = tv.MSUILinearViewWindow(model=waypoints_model)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        self.window.cbTools.currentIndexChanged.emit(1)
        self.wms_control = self.window.docks[0].widget()
        self.wms_control.multilayers.cbWMS_URL.setEditText("")
        yield
        self.window.hide()
        shutil.rmtree(self.tempdir)

    def query_server(self, url, qtbot):
        QtTest.QTest.keyClicks(self.wms_control.multilayers.cbWMS_URL, url)
        with qtbot.wait_signal(self.wms_control.cpdlg.canceled):
            QtTest.QTest.mouseClick(self.wms_control.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)

    def test_server_getmap(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(self.url)
        with qtbot.wait_signal(self.wms_control.image_displayed):
            QtTest.QTest.mouseClick(self.wms_control.btGetMap, QtCore.Qt.LeftButton)
