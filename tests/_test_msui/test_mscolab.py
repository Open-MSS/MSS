# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2022 by the MSS team, see AUTHORS.
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
from mslib.utils.config import read_config_file, config_loader
from tests.utils import mscolab_start_server, create_msui_settings_file, ExceptionMock
from mslib.msui import msui
from mslib.msui import mscolab
from mslib.mscolab.mscolab import handle_db_reset
from tests.constants import MSUI_CONFIG_PATH
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation

PORTS = list(range(25000, 25500))


class Test_Mscolab_connect_window():
    def setup_method(self):
        handle_db_reset()
        self._reset_config_file()
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.main_window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.main_window.show()
        self.window = mscolab.MSColab_ConnectDialog(parent=self.main_window, mscolab=self.main_window.mscolab)
        self.window.urlCb.setEditText(self.url)
        self.main_window.mscolab.connect_window = self.window
        self.window.show()

    def teardown_method(self):
        self.main_window.mscolab.logout()
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
        assert self.window.mscolab_server_url is not None
        QtTest.QTest.mouseClick(self.window.connectBtn, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None
        # set ui_name_winodw default
        assert self.main_window.usernameLabel.text() == 'User'

    def test_login(self):
        self._connect_to_mscolab()
        self._login(self.userdata[0], self.userdata[2])
        QtWidgets.QApplication.processEvents()
        # show logged in widgets
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        assert self.main_window.connectBtn.isVisible() is False
        assert self.main_window.mscolab.connect_window is None
        assert self.main_window.local_active is True
        # test operation listing visibility
        assert self.main_window.listOperationsMSC.model().rowCount() == 1

    def test_logout_action_trigger(self):
        # Login
        self._connect_to_mscolab()
        self._login(self.userdata[0], self.userdata[2])
        QtWidgets.QApplication.processEvents()
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        # Logout
        self.main_window.mscolab.logout_action.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.main_window.listOperationsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None
        assert self.main_window.local_active is True
        assert self.main_window.usernameLabel.text() == "User"

    def test_logout(self):
        # Login
        self._connect_to_mscolab()
        self._login(self.userdata[0], self.userdata[2])
        QtWidgets.QApplication.processEvents()
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        # Logout
        self.main_window.mscolab.logout()
        assert self.main_window.usernameLabel.text() == "User"
        assert self.main_window.connectBtn.isVisible() is True
        assert self.main_window.listOperationsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None
        assert self.main_window.local_active is True

    def test_add_user(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        assert config_loader(dataset="MSCOLAB_mailid") == "something@something.org"
        assert config_loader(dataset="MSCOLAB_password") == "something"
        # assert self.window.stackedWidget.currentWidget() == self.window.newuserPage
        assert self.main_window.usernameLabel.text() == 'something'
        assert self.main_window.mscolab.connect_window is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.No)
    def test_add_users_without_updating_credentials_in_config_file(self, mockmessage):
        create_msui_settings_file('{"MSCOLAB_mailid": "something@something.org", "MSCOLAB_password": "something"}')
        read_config_file()
        # check current settings
        assert config_loader(dataset="MSCOLAB_mailid") == "something@something.org"
        assert config_loader(dataset="MSCOLAB_password") == "something"
        self._connect_to_mscolab()
        assert self.window.mscolab_server_url is not None
        self._create_user("anand", "anand@something.org", "anand")
        # check changed settings
        assert config_loader(dataset="MSCOLAB_mailid") == "something@something.org"
        assert config_loader(dataset="MSCOLAB_password") == "something"
        # check user is logged in
        assert self.main_window.usernameLabel.text() == "anand"

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_add_users_with_updating_credentials_in_config_file(self, mockmessage):
        create_msui_settings_file('{"MSCOLAB_mailid": "something@something.org", "MSCOLAB_password": "something"}')
        read_config_file()
        # check current settings
        assert config_loader(dataset="MSCOLAB_mailid") == "something@something.org"
        assert config_loader(dataset="MSCOLAB_password") == "something"
        self._connect_to_mscolab()
        assert self.window.mscolab_server_url is not None
        self._create_user("anand", "anand@something.org", "anand")
        # check changed settings
        assert config_loader(dataset="MSCOLAB_mailid") == "anand@something.org"
        assert config_loader(dataset="MSCOLAB_password") == "anand"
        # check user is logged in
        assert self.main_window.usernameLabel.text() == "anand"

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

    def _reset_config_file(self):
        create_msui_settings_file('{ }')
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Mscolab(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
    # import/export plugins
    import_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"],
        "FliteStar": ["fls", "mslib.plugins.io.flitestar", "load_from_flitestar"],
    }
    export_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
    }

    def setup_method(self):
        handle_db_reset()
        self._reset_config_file()
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

        self.userdata2 = 'sree@sree.org', 'sree', 'sree'
        self.operation_name3 = "kerala"
        assert add_user(self.userdata2[0], self.userdata2[1], self.userdata2[2])
        assert add_operation(self.operation_name3, "test kerala")
        assert add_user_to_operation(path=self.operation_name3, emailid=self.userdata2[0])

        self.userdata3 = 'anand@anand.org', 'anand', 'anand'
        assert add_user(self.userdata3[0], self.userdata3[1], self.userdata3[2])
        assert add_user_to_operation(path=self.operation_name3, access_level="collaborator", emailid=self.userdata3[0])

        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.show()

    def teardown_method(self):
        self.window.mscolab.logout()
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        # force close all open views
        while self.window.listViews.count() > 0:
            self.window.listViews.item(0).window.handle_force_close()
        # close all hanging operation option windows
        self.window.mscolab.close_external_windows()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_activate_operation(self):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        # activate a operation
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_name == self.operation_name

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_view_open(self, mockbox):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        # test after activating operation
        self._activate_operation_at_index(0)
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

        operation = self.window.mscolab.active_op_id
        uid = self.window.mscolab.user["id"]
        active_windows = self.window.get_active_views()
        topview = active_windows[1]
        tableview = active_windows[0]
        self.window.mscolab.handle_update_permission(operation, uid, "viewer")
        assert not tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and not action.isEnabled() for action in topview.mpl.navbar.actions())
        self.window.mscolab.handle_update_permission(operation, uid, "creator")
        assert tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and action.isEnabled() for action in topview.mpl.navbar.actions())

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'),
                              "Flight track (*.ftml)"))
    def test_handle_export(self, mockbox):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        self._activate_operation_at_index(0)
        self.window.actionExportFlightTrackFTML.trigger()
        QtWidgets.QApplication.processEvents()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.mscolab.data_dir,
                                                                       'test_export.ftml'))
        wp_count = len(self.window.mscolab.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.mscolab.waypoints_model.waypoint_data(i).lat

    @pytest.mark.skip("fails on github with WebSocket transport is not available")
    @pytest.mark.parametrize("ext", [".ftml", ".csv", ".txt"])
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_import_file(self, mockbox, ext):
        self.window.remove_plugins()
        with mock.patch("mslib.msui.msui.config_loader", return_value=self.import_plugins):
            self.window.add_import_plugins("qt")
        with mock.patch("mslib.msui.msui.config_loader", return_value=self.export_plugins):
            self.window.add_export_plugins("qt")
        file_path = fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, f'test_import{ext}')
        with mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName", return_value=(file_path, None)):
            with mock.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName", return_value=(file_path, None)):
                self._connect_to_mscolab()
                self._login(emailid=self.userdata[0], password=self.userdata[2])
                self._activate_operation_at_index(0)
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

    @pytest.mark.skip("Runs in a timeout locally > 60s")
    def test_work_locally_toggle(self):
        self._connect_to_mscolab()
        self._login(emailid=self.userdata[0], password=self.userdata[2])
        self._activate_operation_at_index(0)
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

    @pytest.mark.skip("fails often on github on a timeout >60s")
    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    @mock.patch("mslib.msui.mscolab.get_open_filename", return_value=os.path.join(sample_path, u"example.ftml"))
    def test_browse_add_operation(self, mockopen, mockmessage):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self.window.actionAddOperation.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.path.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.description.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.category.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.mscolab.add_proj_dialog.browse, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        # we need to wait for the update of the operation list
        QtTest.QTest.qWait(200)
        QtWidgets.QApplication.processEvents()
        assert self.window.listOperationsMSC.model().rowCount() == 1
        item = self.window.listOperationsMSC.item(0)
        assert item.operation_path == "example"
        assert item.access_level == "creator"

    @mock.patch("PyQt5.QtWidgets.QErrorMessage")
    def test_add_operation(self, mockbox):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        assert self.window.usernameLabel.text() == 'something'
        assert self.window.connectBtn.isVisible() is False
        self._create_operation("Alpha", "Description Alpha")
        assert mockbox.return_value.showMessage.call_count == 1
        with mock.patch("PyQt5.QtWidgets.QLineEdit.text", return_value=None):
            self._create_operation("Alpha2", "Description Alpha")
        with mock.patch("PyQt5.QtWidgets.QTextEdit.toPlainText", return_value=None):
            self._create_operation("Alpha3", "Description Alpha")
        self._create_operation("/", "Description Alpha")
        assert mockbox.return_value.showMessage.call_count == 4
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._create_operation("reproduce-test", "Description Test")
        assert self.window.listOperationsMSC.model().rowCount() == 2
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_operation_name == "Alpha"
        self._activate_operation_at_index(1)
        assert self.window.mscolab.active_operation_name == "reproduce-test"

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information")
    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("flight7", True))
    def test_handle_delete_operation(self, mocktext, mockbox):
        # pytest.skip('needs a review for the delete button pressed. Seems to delete a None operation')
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        operation_name = "flight7"
        self._create_operation(operation_name, "Description flight7")
        # check for operation dir is created on server
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name))
        assert self.window.mscolab.active_op_id is None
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is not None
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self.window.actionDeleteOperation.trigger()
        QtWidgets.QApplication.processEvents()
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is None
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(0)
        # check operation dir name removed
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name)) is False
        assert mockbox.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_handle_leave_operation(self, mockmessage):
        self._connect_to_mscolab()

        self._login(self.userdata3[0], self.userdata3[2])
        QtWidgets.QApplication.processEvents()
        assert self.window.usernameLabel.text() == self.userdata3[1]
        assert self.window.connectBtn.isVisible() is False

        assert self.window.listOperationsMSC.model().rowCount() == 1
        assert self.window.mscolab.active_op_id is None
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is not None

        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 1
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert len(self.window.get_active_views()) == 2

        self.window.actionLeaveOperation.trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(0)
        assert self.window.mscolab.active_op_id is None
        assert self.window.listViews.count() == 0
        assert self.window.listOperationsMSC.model().rowCount() == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information")
    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("new_name", True))
    def test_handle_rename_operation(self, mockbox, mockpatch):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._create_operation("flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionRenameOperation.trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(0)
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_name == "new_name"

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information")
    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("new_desciption", True))
    def test_update_description(self, mockbox, mockpatch):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._create_operation("flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionUpdateOperationDesc.trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(0)
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_desc == "new_desciption"

    def test_get_recent_op_id(self):
        self._connect_to_mscolab()
        self._create_user("anton", "anton@something.org", "something")
        QtTest.QTest.qWait(100)
        assert self.window.usernameLabel.text() == 'anton'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation("flight2", "Description flight2")
        current_op_id = self.window.mscolab.get_recent_op_id()
        self._create_operation("flight3", "Description flight3")
        self._create_operation("flight4", "Description flight4")
        # ToDo fix number after cleanup initial data
        assert self.window.mscolab.get_recent_op_id() == current_op_id + 2

    def test_get_recent_operation(self):
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        QtTest.QTest.qWait(100)
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation("flight1234", "Description flight1234")
        self._activate_operation_at_index(0)
        operation = self.window.mscolab.get_recent_operation()
        assert operation["path"] == "flight1234"
        assert operation["access_level"] == "creator"

    def test_open_chat_window(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._create_operation("flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionChat.trigger()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(0)
        assert self.window.mscolab.chat_window is not None

    def test_close_chat_window(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._create_operation("flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionChat.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.close_chat_window()
        assert self.window.mscolab.chat_window is None

    def test_delete_operation_from_list(self):
        self._connect_to_mscolab()
        self._create_user("other", "other@something.org", "something")
        assert self.window.usernameLabel.text() == 'other'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation("flight3", "Description flight3")
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        self.window.mscolab.delete_operation_from_list(op_id)
        assert self.window.mscolab.active_op_id is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockmessage):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        u_id = self.window.mscolab.user['id']
        self.window.mscolab.open_profile_window()
        QtTest.QTest.mouseClick(self.window.mscolab.profile_dialog.deleteAccountBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listOperationsMSC.model().rowCount() == 0
        assert self.window.usernameLabel.isVisible() is False
        assert self.window.connectBtn.isVisible() is True
        with self.app.app_context():
            assert User.query.filter_by(emailid='something').count() == 0
            assert Permission.query.filter_by(u_id=u_id).count() == 0

    def test_open_help_dialog(self):
        self.window.actionMSColabHelp.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.mscolab.help_dialog is not None

    def test_close_help_dialog(self):
        self.window.actionMSColabHelp.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.mscolab.help_dialog is not None
        QtTest.QTest.mouseClick(
            self.window.mscolab.help_dialog.okayBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(50)
        QtWidgets.QApplication.processEvents()
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

    def _reset_config_file(self):
        create_msui_settings_file('{ }')
        config_file = fs.path.combine(MSUI_CONFIG_PATH, "msui_settings.json")
        read_config_file(path=config_file)

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    def _create_operation(self, path, description, mockbox):
        self.window.actionAddOperation.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.path.setText(str(path))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.description.setText(str(description))
        QtWidgets.QApplication.processEvents()
        self.window.mscolab.add_proj_dialog.category.setText("example")
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_operation_at_index(self, index):
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
