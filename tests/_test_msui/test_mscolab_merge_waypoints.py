# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_merge_waypoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-operation related gui.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import os
import fs
import mock
import pytest

import mslib.utils.auth
from mslib.msui import flighttrack as ft
from mslib.mscolab.conf import mscolab_settings
from PyQt5 import QtCore, QtTest, QtWidgets
from tests.utils import (mscolab_register_and_login, mscolab_create_operation,
                         mscolab_delete_all_operations, mscolab_delete_user)
from mslib.msui import mscolab
from mslib.msui import msui


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Mscolab_Merge_Waypoints:
    @pytest.fixture(autouse=True)
    def setup(self, qapp, mscolab_app, mscolab_server):
        self.app = mscolab_app
        self.url = mscolab_server
        QtTest.QTest.qWait(500)
        self.window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.create_new_flight_track()
        self.emailid = 'merge@alpha.org'
        yield
        self.window.mscolab.logout()
        mslib.utils.auth.del_password_from_keyring("merge@alpha.org")
        with self.app.app_context():
            mscolab_delete_all_operations(self.app, self.url, self.emailid, 'abcdef', 'alpha')
            mscolab_delete_user(self.app, self.url, self.emailid, 'abcdef')
        with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as mss_dir:
            if mss_dir.exists('local_mscolab_data'):
                mss_dir.removetree('local_mscolab_data')
            assert mss_dir.exists('local_mscolab_data') is False
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        QtWidgets.QApplication.processEvents()

    def _create_user_data(self, emailid='merge@alpha.org'):
        with self.app.app_context():
            self._connect_to_mscolab()
            response = mscolab_register_and_login(self.app, self.url, emailid, 'abcdef', 'alpha')

            assert response.status == '200 OK'
            data, response = mscolab_create_operation(self.app, self.url, response,
                                                      path='f3', description='f3 test example')
            assert response.status == '200 OK'
            self._login(emailid, 'abcdef')
            self._activate_operation_at_index(0)

    def _connect_to_mscolab(self):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self, emailid="merge_waypoints_user", password="password"):
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _activate_operation_at_index(self, index):
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _select_waypoints(self, table):
        for row in range(table.model().rowCount()):
            table.selectRow(row)
            QtWidgets.QApplication.processEvents()


class AutoClickOverwriteMscolabMergeWaypointsDialog(mslib.msui.mscolab.MscolabMergeWaypointsDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overwriteBtn.animateClick()


class Test_Overwrite_To_Server(Test_Mscolab_Merge_Waypoints):
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_overwrite_to_server(self, mockbox):
        self.emailid = "save_overwrite@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckbox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # trigger save to server action from server options combobox
        with mock.patch(
            "mslib.msui.mscolab.MscolabMergeWaypointsDialog",
                AutoClickOverwriteMscolabMergeWaypointsDialog):
            self.window.serverOptionsCb.setCurrentIndex(2)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test self.window.waypoints_model not working
        server_xml = self.window.mscolab.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_local_wp.lat
        self.window.workLocallyCheckbox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_server_wp = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_server_wp.lat


class AutoClickKeepMscolabMergeWaypointsDialog(mslib.msui.mscolab.MscolabMergeWaypointsDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keepServerBtn.animateClick()


class Test_Save_Keep_Server_Points(Test_Mscolab_Merge_Waypoints):
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_keep_server_points(self, mockbox):
        self.emailid = "save_keepe@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckbox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # trigger save to server action from server options combobox
        with mock.patch("mslib.msui.mscolab.MscolabMergeWaypointsDialog", AutoClickKeepMscolabMergeWaypointsDialog):
            self.window.serverOptionsCb.setCurrentIndex(2)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test self.window.waypoints_model not working
        server_xml = self.window.mscolab.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model.waypoint_data(0)

        assert wp_local_before.lat != new_local_wp.lat
        assert new_local_wp.lat == wp_server_before.lat
        self.window.workLocallyCheckbox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_server_wp = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat == new_server_wp.lat


class Test_Fetch_From_Server(Test_Mscolab_Merge_Waypoints):
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_fetch_from_server(self, mockbox):
        self.emailid = "fetch_from_server@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckbox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.mscolab.waypoints_model.invert_direction()
        wp_local_before = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # trigger save to server action from server options combobox
        with mock.patch("mslib.msui.mscolab.MscolabMergeWaypointsDialog", AutoClickKeepMscolabMergeWaypointsDialog):
            self.window.serverOptionsCb.setCurrentIndex(1)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test of self.window.waypoints_model not working
        server_xml = self.window.mscolab.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model
        assert len(new_local_wp.waypoints) == 2
        assert new_local_wp.waypoint_data(0).lat == wp_server_before.lat
        self.window.workLocallyCheckbox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert self.window.mscolab.waypoints_model.waypoint_data(0).lat == wp_server_before.lat
