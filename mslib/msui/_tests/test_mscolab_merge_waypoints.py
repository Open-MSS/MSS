# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_merge_waypoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
import sys
import fs
import mock
import pytest

from mslib.msui import flighttrack as ft
from mslib.mscolab.conf import mscolab_settings
from mslib.msui.mscolab import MSSMscolabWindow
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib._tests.utils import (mscolab_start_server, mscolab_register_and_login, mscolab_create_project,
                                mscolab_delete_all_projects, mscolab_delete_user)


PORTS = list(range(9551, 9570))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Mscolab_Merge_Waypoints(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.emailid = 'merge@alpha.org'

    def teardown(self):
        with self.app.app_context():
            mscolab_delete_all_projects(self.app, self.url, self.emailid, 'abcdef', 'alpha')
            mscolab_delete_user(self.app, self.url, self.emailid, 'abcdef')
        with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as mss_dir:
            if mss_dir.exists('local_mscolab_data'):
                mss_dir.removetree('local_mscolab_data')
            assert mss_dir.exists('local_mscolab_data') is False
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def _create_user_data(self, emailid='merge@alpha.org'):
        with self.app.app_context():
            self._connect_to_mscolab()
            response = mscolab_register_and_login(self.app, self.url, emailid, 'abcdef', 'alpha')

            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f3', description='f3 test example')
            assert response.status == '200 OK'
            self._login(emailid, 'abcdef')
            self._activate_project_at_index(0)

    def _connect_to_mscolab(self):
        self.window.url.setEditText(self.url)
        QtTest.QTest.mouseClick(self.window.toggleConnectionBtn, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(100)

    def _login(self, emailid="merge_waypoints_user", password="password"):
        self.window.emailid.setText(emailid)
        self.window.password.setText(password)
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _select_waypoints(self, table):
        for row in range(table.model().rowCount()):
            table.selectRow(row)
            QtWidgets.QApplication.processEvents()


class Test_Overwrite_To_Server(Test_Mscolab_Merge_Waypoints):
    @pytest.mark.skip("skipped because of unhandled message box")
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_overwrite_to_server(self, mockbox):
        pytest.skip("probably a timing problem, fails sometimes")
        self.emailid = "save_overwrite@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # ToDo mock this messagebox
        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.overwriteBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(100)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=2)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test self.window.waypoints_model not working
        server_xml = self.window.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_local_wp.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_server_wp.lat


class Test_Save_Keep_Server_Points(Test_Mscolab_Merge_Waypoints):
    @pytest.mark.skip("skipped because of unhandled message box")
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_keep_server_points(self, mockbox):
        self.emailid = "save_keepe@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # ToDo mock this messagebox
        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(100)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test self.window.waypoints_model not working
        server_xml = self.window.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model.waypoint_data(0)

        assert wp_local_before.lat != new_local_wp.lat
        assert new_local_wp.lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat == new_server_wp.lat


class Test_Fetch_From_Server(Test_Mscolab_Merge_Waypoints):
    @pytest.mark.skip("skipped because of unhandled message box")
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_fetch_from_server(self, mockbox):
        self.emailid = "fetch_from_server@alpha.org"
        self._create_user_data(emailid=self.emailid)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        # ToDo mock this messagebox
        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(100)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test of self.window.waypoints_model not working
        server_xml = self.window.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model
        assert len(new_local_wp.waypoints) == 2
        assert new_local_wp.waypoint_data(0).lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert self.window.waypoints_model.waypoint_data(0).lat == wp_server_before.lat
