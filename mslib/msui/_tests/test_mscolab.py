# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab
    ~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

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
import logging
import sys
import time
import mock

import fs

from mslib.mscolab.demodata import create_test_files
from mslib.msui.flighttrack import WaypointsTableModel
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.mss_qt import QtCore, QtTest, QtWidgets


class Test_Mscolab(object):
    def setup(self):
        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=MSCOLAB_URL_TEST)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        create_test_files()

    def teardown(self):
        # to disconnect connections, and clear token
        self.window.disconnect_handler()
        QtWidgets.QApplication.processEvents()
        self.window.close()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        with fs.open_fs(mscolab_settings.MSCOLAB_DATA_DIR) as mss_dir:
            if mss_dir.exists('local_mscolab_data'):
                mss_dir.removetree('local_mscolab_data')

    def test_url_combo(self):
        assert self.window.url.count() >= 1

    def test_login(self):
        self._login()
        # screen shows logout button
        assert self.window.loggedInWidget.isVisible() is True
        assert self.window.loginWidget.isVisible() is False
        # test project listing visibility
        assert self.window.listProjects.model().rowCount() == 1
        # test logout
        QtTest.QTest.mouseClick(self.window.logoutButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.loggedInWidget.isVisible() is False
        assert self.window.loginWidget.isVisible() is True

    def test_disconnect(self):
        self._connect_to_mscolab()
        QtTest.QTest.mouseClick(self.window.disconnectMscolab, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None

    def test_activate_project(self):
        self._login()
        # activate a project
        self._activate_project_at_index(0)
        assert self.window.active_pid is not None

    def test_view_open(self):
        self._login()
        # test without activating project
        QtTest.QTest.mouseClick(self.window.topview, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.sideview, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.tableview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 0
        # test after activating project
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.tableview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 1
        QtTest.QTest.mouseClick(self.window.topview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 2
        QtTest.QTest.mouseClick(self.window.sideview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 3

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'), None))
    def test_export_file(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.exportBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.data_dir, 'test_export.ftml'))
        wp_count = len(self.window.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.waypoints_model.waypoint_data(i).lat

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_import.ftml'), None))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_import.ftml'), None))
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_import_file(self, mockExport, mockImport, mockMessage):
        # TODO: CHECK WHY GIT LOCK ERROR COMES
        self._login()
        self._activate_project_at_index(0)
        exported_wp = WaypointsTableModel(waypoints=self.window.waypoints_model.waypoints)
        QtTest.QTest.mouseClick(self.window.exportBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        assert exported_wp.waypoint_data(0).lat != self.window.waypoints_model.waypoint_data(0).lat
        QtTest.QTest.mouseClick(self.window.importBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        assert len(self.window.waypoints_model.waypoints) == 2
        imported_wp = self.window.waypoints_model
        wp_count = len(imported_wp.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_wp.waypoint_data(i).lat == imported_wp.waypoint_data(i).lat

    def test_work_locally_toggle(self):
        self._login()
        self._activate_project_at_index(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wpdata_local = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wpdata_server = self.window.waypoints_model.waypoint_data(0)
        assert wpdata_local.lat != wpdata_server.lat

    # TODO: THESE TESTS WORK INDIVIDUALLY BUT NOT WHEN THE TEST SUITE IS RUN
    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_overwrite_to_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            merge_dialog = QtWidgets.QApplication.activeWindow()
            QtTest.QTest.mouseClick(merge_dialog.overwriteBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()

        QtCore.QTimer.singleShot(2000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_local_wp.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat == new_server_wp.lat

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_keep_server_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat

        def handle_merge_dialog():
            merge_dialog = QtWidgets.QApplication.activeWindow()
            QtTest.QTest.mouseClick(merge_dialog.keepServerBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(2000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_local_before.lat != new_local_wp.lat
        assert new_local_wp.lat == wp_server_before.lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat == new_server_wp.lat

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_save_merge_points(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        self.window.waypoints_model.invert_direction()
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            merge_dialog = QtWidgets.QApplication.activeWindow()
            self._select_waypoints(merge_dialog.localWaypointsTable)
            self._select_waypoints(merge_dialog.serverWaypointsTable)
            merge_waypoints_model = merge_dialog.merge_waypoints_model
            QtTest.QTest.mouseClick(merge_dialog.saveBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(2000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model
        assert len(new_server_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_server_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_fetch_from_server(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        wp_server_before = self.window.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        wp_local = self.window.waypoints_model.waypoint_data(0)
        assert wp_local.lat == wp_server_before.lat
        self.window.waypoints_model.invert_direction()
        wp_local_before = self.window.waypoints_model.waypoint_data(0)
        assert wp_server_before.lat != wp_local_before.lat
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            merge_dialog = QtWidgets.QApplication.activeWindow()
            self._select_waypoints(merge_dialog.localWaypointsTable)
            self._select_waypoints(merge_dialog.serverWaypointsTable)
            merge_waypoints_model = merge_dialog.merge_waypoints_model
            QtTest.QTest.mouseClick(merge_dialog.saveBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            time.sleep(2)

        QtCore.QTimer.singleShot(2000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        new_local_wp = self.window.waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat

        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        new_server_wp = self.window.waypoints_model
        assert len(new_server_wp.waypoints) == 2
    # ================================================================================================

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockbox):
        self._login()
        QtTest.QTest.mouseClick(self.window.deleteAccountButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.listProjects) == 0
        assert self.window.loggedInWidget.isVisible() is False
        assert self.window.loginWidget.isVisible() is True

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self, emailid="mscolab_user", password="password"):
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
