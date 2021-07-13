# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

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
import sys
import os
import fs
import fs.errors
import fs.opener.errors
import requests.exceptions
import mock
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Permission, User
from mslib.msui.flighttrack import WaypointsTableModel
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib._tests.utils import mscolab_start_server
import mslib.msui.mss_pyui as mss_pyui
from mslib.msui import mscolab


PORTS = list(range(9481, 9530))


class Test_Mscolab_connect_window():
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.main_window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.main_window.show()
        self.window = mscolab.MSColab_ConnectDialog(parent=self.main_window, mscolab=self.main_window.mscolab)
        self.window.urlCb.setEditText(self.url)
        self.main_window.mscolab.connect_window = self.window

    def teardown(self):
        self.window.hide()
        self.main_window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_url_combo(self):
        assert self.window.urlCb.count() >= 1

    def test_disconnect(self):
        self._connect_to_mscolab()
        QtTest.QTest.mouseClick(self.window.connectBtn, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None

    def test_login(self):
        self._connect_to_mscolab()
        self._login()
        QtWidgets.QApplication.processEvents()
        # show logged in widgets
        assert self.main_window.usernameLabel.text() == 'a'
        assert self.main_window.connectBtn.isVisible() is False
        assert self.main_window.mscolab.connect_window is None
        # test project listing visibility
        assert self.main_window.listProjectsMSC.model().rowCount() == 3
        # test logout
        self.main_window.mscolab.logout_action.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.main_window.listProjectsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None

    def test_add_user(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        # assert self.window.stackedWidget.currentWidget() == self.window.newuserPage
        self._login("something@something.org", "something")
        assert self.main_window.usernameLabel.text() == 'something'
        assert self.main_window.mscolab.connect_window is None

    def _connect_to_mscolab(self):
        self.window.urlCb.setEditText(self.url)
        QtTest.QTest.mouseClick(self.window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self, emailid="a", password="a"):
        self.window.loginEmailLe.setText(emailid)
        self.window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.window.loginBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _create_user(self, username, email, password):
        QtTest.QTest.mouseClick(self.window.addUserBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.newUsernameLe.setText(str(username))
        QtWidgets.QApplication.processEvents()
        self.window.newEmailLe.setText(str(email))
        QtWidgets.QApplication.processEvents()
        self.window.newPasswordLe.setText(str(password))
        QtWidgets.QApplication.processEvents()
        self.window.newConfirmPasswordLe.setText(str(password))
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.newUserBb.button(self.window.newUserBb.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Mscolab(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")

    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.show()

    def teardown(self):
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_activate_project(self):
        self._connect_to_mscolab()
        self._login()
        # activate a project
        self._activate_project_at_index(0)
        assert self.window.mscolab.active_pid is not None

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_view_open(self, mockbox):
        self._connect_to_mscolab()
        self._login()
        # test after activating project
        self._activate_project_at_index(0)
        self.window.actionTableView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 1
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 2
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 3
        self.window.actionLinearView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 4

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'), None))
    def test_handle_export(self, mockbox):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        self.window.actionExportFlightTrackFTML.trigger()
        QtWidgets.QApplication.processEvents()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.mscolab.data_dir, 'test_export.ftml'))
        wp_count = len(self.window.mscolab.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.mscolab.waypoints_model.waypoint_data(i).lat

    @pytest.mark.parametrize("ext", [".ftml", ".txt"])
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_import_file(self, mockExport, mockImport, mockMessage):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        exported_wp = WaypointsTableModel(waypoints=self.window.mscolab.waypoints_model.waypoints)
        self.window.actionExportFlightTrackFTML.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert exported_wp.waypoint_data(0).lat != self.window.mscolab.waypoints_model.waypoint_data(0).lat
        self.window.actionImportFlightTrackFTML.trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert len(self.window.mscolab.waypoints_model.waypoints) == 2
        imported_wp = self.window.mscolab.waypoints_model
        wp_count = len(imported_wp.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_wp.waypoint_data(i).lat == imported_wp.waypoint_data(i).lat

    def test_work_locally_toggle(self):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        self.window.workLocallyCheckbox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wpdata_local = self.window.mscolab.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckbox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        wpdata_server = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wpdata_local.lat != wpdata_server.lat

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    @mock.patch("mslib.msui.mscolab.get_open_filename", return_value=os.path.join(sample_path, u"example.ftml"))
    def test_browse_add_project(self, mockopen, mockmessage):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        assert self.window.listProjectsMSC.model().rowCount() == 0
        self.window.actionAddProject.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.path.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.description.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mscolab.add_proj_dialog.browse, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjectsMSC.model().rowCount() == 1

    @mock.patch("PyQt5.QtWidgets.QErrorMessage")
    def test_add_project(self, mockbox):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        assert self.window.usernameLabel.text() == 'something'
        assert self.window.connectBtn.isVisible() is False
        self._create_project("Alpha", "Description Alpha")
        assert self.window.listProjectsMSC.model().rowCount() == 1

    @mock.patch("mslib.msui.mscolab.QtWidgets.QInputDialog.getText", return_value=("flight7", True))
    def test_handle_delete_project(self, mocktext):
        # pytest.skip('needs a review for the delete button pressed. Seems to delete a None project')
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        self._login("berta@something.org", "something")
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listProjectsMSC.model().rowCount() == 0
        self._create_project("flight7", "Description flight7")
        assert self.window.mscolab.active_pid is None
        self._activate_project_at_index(0)
        p_id = self.window.mscolab.get_recent_pid()
        assert p_id is not None
        assert self.window.listProjectsMSC.model().rowCount() == 1
        self.window.actionDeleteProject.trigger()
        QtWidgets.QApplication.processEvents()
        p_id = self.window.mscolab.get_recent_pid()
        assert p_id is None

    def test_get_recent_pid(self):
        self._connect_to_mscolab()
        self._create_user("anton", "anton@something.org", "something")
        self._login("anton@something.org", "something")
        assert self.window.usernameLabel.text() == 'anton'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listProjectsMSC.model().rowCount() == 0
        self._create_project("flight2", "Description flight2")
        current_pid = self.window.mscolab.get_recent_pid()
        self._create_project("flight3", "Description flight3")
        self._create_project("flight4", "Description flight4")
        # ToDo fix number after cleanup initial data
        assert self.window.mscolab.get_recent_pid() == current_pid + 2

    def test_get_recent_project(self):
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        self._login("berta@something.org", "something")
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listProjectsMSC.model().rowCount() == 0
        self._create_project("flight1234", "Description flight1234")
        self._activate_project_at_index(0)
        project = self.window.mscolab.get_recent_project()
        assert project["path"] == "flight1234"
        assert project["access_level"] == "creator"

    def test_delete_project_from_list(self):
        self._connect_to_mscolab()
        self._create_user("other", "other@something.org", "something")
        self._login("other@something.org", "something")
        assert self.window.usernameLabel.text() == 'other'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listProjectsMSC.model().rowCount() == 0
        self._create_project("flight3", "Description flight3")
        self._activate_project_at_index(0)
        p_id = self.window.mscolab.get_recent_pid()
        self.window.mscolab.delete_project_from_list(p_id)
        assert self.window.mscolab.active_pid is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockmessage):
        pytest.skip("To be done")
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        u_id = self.window.user['id']
        QtTest.QTest.mouseClick(self.window.deleteAccountButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.listProjects) == 0
        assert self.window.loggedInWidget.isVisible() is False
        with self.app.app_context():
            assert User.query.filter_by(emailid='something').count() == 0
            assert Permission.query.filter_by(u_id=u_id).count() == 0

    def test_open_help_dialog(self):
        pytest.skip("To be done")
        QtTest.QTest.mouseClick(self.window.helpBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.help_dialog is not None
        self.window.close()

    def test_close_help_dialog(self):
        pytest.skip("To be done")
        QtTest.QTest.mouseClick(self.window.helpBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.close()
        assert self.window.help_dialog is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("sys.exit")
    def test_create_dir_exceptions(self, mockexit, mockbox):
        with mock.patch("fs.open_fs", new=ExceptionMock(fs.errors.CreateFailed).raise_exc):
            self.window.data_dir = "://"
            self.window.create_dir()
            assert mockbox.critical.call_count == 1
            assert mockexit.call_count == 1

        with mock.patch("fs.open_fs", new=ExceptionMock(fs.opener.errors.UnsupportedProtocol).raise_exc):
            self.window.data_dir = "://"
            self.window.create_dir()
            assert mockbox.critical.call_count == 2
            assert mockexit.call_count == 2

    def _connect_to_mscolab(self):
        self.window.mscolab.open_connect_window()
        self.connect_window = self.window.mscolab.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self, emailid="a", password="a"):
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _create_user(self, username, email, password):
        QtTest.QTest.mouseClick(self.connect_window.addUserBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.connect_window.newUsernameLe.setText(str(username))
        QtWidgets.QApplication.processEvents()
        self.connect_window.newEmailLe.setText(str(email))
        QtWidgets.QApplication.processEvents()
        self.connect_window.newPasswordLe.setText(str(password))
        QtWidgets.QApplication.processEvents()
        self.connect_window.newConfirmPasswordLe.setText(str(password))
        QtWidgets.QApplication.processEvents()
        okWidget = self.connect_window.newUserBb.button(self.connect_window.newUserBb.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    def _create_project(self, path, description, mockbox):
        self.window.actionAddProject.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.path.setText(str(path))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.description.setText(str(description))
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjectsMSC.item(index)
        point = self.window.listProjectsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
