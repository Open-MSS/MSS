# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_merge_waypoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
import sys
import time

import fs
import mock
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.msui.mscolab import MSSMscolabWindow
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9551, 9570))


@pytest.mark.skip('these tests run on direct call')
class Test_Mscolab(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(1)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.window.show()

    def teardown(self):
        with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as mss_dir:
            if mss_dir.exists('local_mscolab_data'):
                mss_dir.removetree('local_mscolab_data')
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.close()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

        # self.application.quit()
        # QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_overwrite_to_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.overwriteBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_local_wp.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_server_wp.lat

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_keep_server_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(1)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat != new_local_wp.lat
        assert new_local_wp.lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat == new_server_wp.lat

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_merge_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        self.window.waypoints_model.invert_direction()
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            self._select_waypoints(self.window.merge_dialog.localWaypointsTable)
            self._select_waypoints(self.window.merge_dialog.serverWaypointsTable)
            merge_waypoints_model = self.window.merge_dialog.merge_waypoints_model
            QtTest.QTest.mouseClick(self.window.merge_dialog.saveBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(1)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        new_server_wp = self.window.waypoints_model
        assert len(new_server_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_server_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_fetch_from_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            QtTest.QTest.mouseClick(self.window.merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(1)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        assert len(new_local_wp.waypoints) == 2
        assert new_local_wp.waypoint_data(0).lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        assert self.window.waypoints_model.waypoint_data(0).lat == wp_server_before.lat

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self, emailid="merge_waypoints_user", password="password"):
        self._connect_to_mscolab()
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
