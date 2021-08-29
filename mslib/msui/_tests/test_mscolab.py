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
from mslib._tests.utils import mscolab_start_server, ExceptionMock
import mslib.msui.mss_pyui as mss_pyui
from mslib.msui import mscolab
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.seed import add_user, get_user, add_project, add_user_to_project

PORTS = list(range(9481, 9530))


class Test_Mscolab_connect_window():
    def setup(self):
        handle_db_reset()
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.room_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, "test europe")
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.main_window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.main_window.show()
        self.window = mscolab.MSColab_ConnectDialog(parent=self.main_window, mscolab=self.main_window.mscolab)
        self.window.urlCb.setEditText(self.url)
        self.main_window.mscolab.connect_window = self.window
        self.window.show()

    def teardown(self):
        self.window.hide()
        self.main_window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_url_combo(self):
        assert self.window.urlCb.count() >= 1

    @mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet")
    def test_connect(self, mockset):
        for exc in [requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema,
                    requests.exceptions.InvalidURL, requests.exceptions.SSLError, Exception("")]:
            with mock.patch("requests.get", new=ExceptionMock(exc).raise_exc):
                self.window.connect_handler()

        self._connect_to_mscolab()
        assert mockset.call_args_list == [mock.call("color: red;") for _ in range(5)] + [mock.call("color: green;")]

    def test_disconnect(self):
        self._connect_to_mscolab()
        QtTest.QTest.mouseClick(self.window.connectBtn, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None

    # @pytest.mark.skip("fails on github")
    def test_login(self):
        self._connect_to_mscolab()
        self._login(self.userdata[0], self.userdata[2])
        QtWidgets.QApplication.processEvents()
        # show logged in widgets
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        assert self.main_window.connectBtn.isVisible() is False
        assert self.main_window.mscolab.connect_window is None
        assert self.main_window.local_active is True
        # test project listing visibility
        assert self.main_window.listProjectsMSC.model().rowCount() == 1
        # test logout
        self.main_window.mscolab.logout_action.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.main_window.listProjectsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None
        assert self.main_window.local_active is True

    # @pytest.mark.skip("fails on github")
    def test_add_user(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        # assert self.window.stackedWidget.currentWidget() == self.window.newuserPage
        self._login("something@something.org", "something")
        assert self.main_window.usernameLabel.text() == 'something'
        assert self.main_window.mscolab.connect_window is None

    # @pytest.mark.skip("fails on github")
    def test_failed_authorize(self):
        class response:
            def __init__(self, code, text):
                self.status_code = code
                self.text = text

        # case: connection error when trying to login after connecting to server
        self._connect_to_mscolab()
        with mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet") as mockset:
            with mock.patch("requests.Session.post", new=ExceptionMock(requests.exceptions.ConnectionError).raise_exc):
                self._login()
                mockset.assert_has_calls([mock.call("color: red;"), mock.call("")])

        # case: when the credentials are incorrect for login
        self._connect_to_mscolab()
        with mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet") as mockset:
            with mock.patch("requests.Session.post", return_value=response(201, "False")):
                self._login()
                mockset.assert_has_calls([mock.call("color: red;")])

        # case: when http auth fails
        with mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet") as mockset:
            with mock.patch("requests.Session.post", return_value=response(401, "Unauthorized Access")):
                self._login()
                # check if switched to HTTP Auth Page
                assert self.window.stackedWidget.currentIndex() == 2
                # press ok without entering server auth details
                okWidget = self.window.httpBb.button(self.window.httpBb.Ok)
                QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
                QtWidgets.QApplication.processEvents()
                mockset.assert_has_calls([mock.call("color: red;")])

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
    # import/export plugins
    import_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"],
        "FliteStar": ["fls", "mslib.plugins.io.flitestar", "load_from_flitestar"],
    }
    export_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
    }

    def setup(self):
        handle_db_reset()
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.room_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, "test europe")
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.show()

    def teardown(self):
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        # force close all open views
        while self.window.listViews.count() > 0:
            self.window.listViews.item(0).window.handle_force_close()
        # close all hanging project option windows
        self.window.mscolab.close_external_windows()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_activate_project(self):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        # activate a project
        self._activate_project_at_index(0)
        assert self.window.mscolab.active_pid is not None
        assert self.window.mscolab.active_project_name == self.room_name

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_view_open(self, mockbox):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
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

        project = self.window.mscolab.active_pid
        uid = self.window.mscolab.user["id"]
        active_windows = self.window.get_active_views()
        topview = active_windows[1]
        tableview = active_windows[0]
        self.window.mscolab.handle_update_permission(project, uid, "viewer")
        assert not tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and not action.isEnabled() for action in topview.mpl.navbar.actions())
        self.window.mscolab.handle_update_permission(project, uid, "creator")
        assert tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and action.isEnabled() for action in topview.mpl.navbar.actions())

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'), None))
    def test_handle_export(self, mockbox):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        self._activate_project_at_index(0)
        self.window.actionExportFlightTrackftml.trigger()
        QtWidgets.QApplication.processEvents()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.mscolab.data_dir,
                                                                       'test_export.ftml'))
        wp_count = len(self.window.mscolab.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.mscolab.waypoints_model.waypoint_data(i).lat

    # @pytest.mark.skip("fails on github")
    @pytest.mark.parametrize("ext", [".ftml", ".csv", ".txt"])
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_import_file(self, mockbox, ext):
        with mock.patch("mslib.msui.mss_pyui.config_loader", return_value=self.import_plugins):
            self.window.add_import_plugins("qt")
        with mock.patch("mslib.msui.mss_pyui.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        file_path = fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, f'test_import{ext}')
        with mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName", return_value=(file_path, None)):
            with mock.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName", return_value=(file_path, None)):
                self._connect_to_mscolab()
                self._login(emailid=self.userdata[0], password=self.userdata[2])
                self._activate_project_at_index(0)
                exported_wp = WaypointsTableModel(waypoints=self.window.mscolab.waypoints_model.waypoints)
                full_name = f"actionExportFlightTrack{ext[1:]}"
                for action in self.window.menuExportActiveFlightTrack.actions():
                    if action.objectName() == full_name:
                        action.trigger()
                        break
                assert os.path.exists(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, f'test_import{ext}'))
                QtWidgets.QApplication.processEvents()
                self.window.mscolab.waypoints_model.invert_direction()
                QtWidgets.QApplication.processEvents()
                QtTest.QTest.qWait(100)
                assert exported_wp.waypoint_data(0).lat != self.window.mscolab.waypoints_model.waypoint_data(0).lat
                full_name = f"actionImportFlightTrack{ext[1:]}"
                for action in self.window.menuImportFlightTrack.actions():
                    if action.objectName() == full_name:
                        action.trigger()
                        break
                QtWidgets.QApplication.processEvents()
                QtTest.QTest.qWait(100)
                assert len(self.window.mscolab.waypoints_model.waypoints) == 2
                imported_wp = self.window.mscolab.waypoints_model
                wp_count = len(imported_wp.waypoints)
                assert wp_count == 2
                for i in range(wp_count):
                    assert exported_wp.waypoint_data(i).lat == imported_wp.waypoint_data(i).lat

    # @pytest.mark.skip("fails on github")
    def test_work_locally_toggle(self):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
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

    # @pytest.mark.skip("fails on github")
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
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjectsMSC.model().rowCount() == 1

    # @pytest.mark.skip("fails on github")
    @mock.patch("PyQt5.QtWidgets.QErrorMessage")
    def test_add_project(self, mockbox):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        assert self.window.usernameLabel.text() == 'something'
        assert self.window.connectBtn.isVisible() is False
        self._create_project("Alpha", "Description Alpha")
        assert mockbox.return_value.showMessage.call_count == 1
        with mock.patch("PyQt5.QtWidgets.QLineEdit.text", return_value=None):
            self._create_project("Alpha2", "Description Alpha")
        with mock.patch("PyQt5.QtWidgets.QTextEdit.toPlainText", return_value=None):
            self._create_project("Alpha3", "Description Alpha")
        self._create_project("/", "Description Alpha")
        assert mockbox.return_value.showMessage.call_count == 4
        assert self.window.listProjectsMSC.model().rowCount() == 1
        self._create_project("reproduce-test", "Description Test")
        assert self.window.listProjectsMSC.model().rowCount() == 2
        self._activate_project_at_index(0)
        assert self.window.mscolab.active_project_name == "Alpha"
        self._activate_project_at_index(1)
        assert self.window.mscolab.active_project_name == "reproduce-test"

    @mock.patch("mslib.msui.mscolab.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mscolab.QtWidgets.QInputDialog.getText", return_value=("flight7", True))
    def test_handle_delete_project(self, mocktext, mockbox):
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
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        u_id = self.window.mscolab.user['id']
        self.window.mscolab.open_profile_window()
        QtTest.QTest.mouseClick(self.window.mscolab.profile_dialog.deleteAccountBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjectsMSC.model().rowCount() == 0
        assert self.window.usernameLabel.isVisible() is False
        assert self.window.connectBtn.isVisible() is True
        with self.app.app_context():
            assert User.query.filter_by(emailid='something').count() == 0
            assert Permission.query.filter_by(u_id=u_id).count() == 0

    def test_open_help_dialog(self):
        self.window.actionMSColabHelp.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.mscolab.help_dialog is not None
        self.window.close()

    @mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes)
    def test_close_help_dialog(self, mockwarn):
        self.window.actionMSColabHelp.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.close()
        QtTest.QTest.qWait(50)
        assert self.window.mscolab.help_dialog is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("sys.exit")
    def test_create_dir_exceptions(self, mockexit, mockbox):
        with mock.patch("fs.open_fs", new=ExceptionMock(fs.errors.CreateFailed).raise_exc):
            self.window.mscolab.data_dir = "://"
            self.window.mscolab.create_dir()
            assert mockbox.critical.call_count == 1
            assert mockexit.call_count == 1

        with mock.patch("fs.open_fs", new=ExceptionMock(fs.opener.errors.UnsupportedProtocol).raise_exc):
            self.window.mscolab.data_dir = "://"
            self.window.mscolab.create_dir()
            assert mockbox.critical.call_count == 2
            assert mockexit.call_count == 2

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_profile_dialog(self, mockbox):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        self.window.mscolab.profile_action.trigger()
        QtWidgets.QApplication.processEvents()
        # case: default gravatar is set and no messagebox is called
        assert mockbox.critical.call_count == 0
        assert self.window.mscolab.prof_diag is not None
        # case: trying to fetch non-existing gravatar
        self.window.mscolab.fetch_gravatar(refresh=True)
        assert mockbox.critical.call_count == 1
        assert not self.window.mscolab.profile_dialog.gravatarLabel.pixmap().isNull()

    def _connect_to_mscolab(self):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self, emailid, password):
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
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjectsMSC.item(index)
        point = self.window.listProjectsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
