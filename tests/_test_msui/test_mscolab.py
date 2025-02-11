# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import fs.errors
import fs.opener.errors
import requests.exceptions
import mock
import pytest

import mslib.utils.auth
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Permission, User
from mslib.msui.flighttrack import WaypointsTableModel
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.utils.config import read_config_file, config_loader, modify_config_file
from tests.utils import create_msui_settings_file, ExceptionMock
from mslib.msui import msui
from mslib.msui import mscolab
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation


class Test_Mscolab_connect_window:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mscolab_server):
        self.url = mscolab_server
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

        self.main_window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.main_window.create_new_flight_track()
        self.main_window.show()
        self.window = mscolab.MSColab_ConnectDialog(parent=self.main_window, mscolab=self.main_window.mscolab)
        self.window.urlCb.setEditText(self.url)
        self.main_window.mscolab.connect_window = self.window
        self.window.show()
        for email in ["something@something.org", "anand@something.org",
                      "berta@something.org", "anton@something.org",
                      "other@something.org"]:
            mslib.utils.auth.del_password_from_keyring(service_name="MSCOLAB", username=email)
        yield
        self.main_window.mscolab.logout()
        self.window.hide()
        self.main_window.hide()

    def test_url_combo(self):
        assert self.window.urlCb.count() >= 1

    @pytest.mark.parametrize(
        "exc",
        [requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema,
         requests.exceptions.InvalidURL, requests.exceptions.SSLError,
         Exception])
    @mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet")
    def test_connect_except(self, mockset, exc):
        with mock.patch("requests.Session.get", new=ExceptionMock(exc).raise_exc):
            self.window.connect_handler()
        assert mockset.call_args_list == [mock.call("color: red;")]

    @mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet")
    def test_connect_denied(self, mockset):
        with mock.patch("requests.Session.get", return_value=mock.Mock(status_code=401)):
            self.window.connect_handler()
        assert mockset.call_args_list == [mock.call("color: red;")]

    @mock.patch("PyQt5.QtWidgets.QWidget.setStyleSheet")
    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.No)
    def test_connect_success(self, mockbox, mockset, qtbot):
        assert mslib.utils.auth.get_password_from_keyring("MSCOLAB_AUTH_" + self.url, "mscolab") != "fnord"
        self._connect_to_mscolab(qtbot, password="fnord")

        assert mslib.utils.auth.get_password_from_keyring("MSCOLAB_AUTH_" + self.url, "mscolab") == "fnord"
        assert mockset.call_args_list == [mock.call("color: green;")]

    def test_disconnect(self, qtbot):
        self._connect_to_mscolab(qtbot)
        assert self.window.mscolab_server_url is not None
        QtTest.QTest.mouseClick(self.window.disconnectBtn, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None
        # set ui_name_winodw default
        assert self.main_window.usernameLabel.text() == 'User'

    def test_login(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, self.userdata[0], self.userdata[2])

        def assert_():
            # show logged in widgets
            assert self.main_window.usernameLabel.text() == self.userdata[1]
            assert self.main_window.connectBtn.isVisible() is False
            assert self.main_window.mscolab.connect_window is None
            assert self.main_window.local_active is True
            # test operation listing visibility
            assert self.main_window.listOperationsMSC.model().rowCount() == 1
        qtbot.wait_until(assert_)

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_login_with_different_account_shows_update_credentials_popup(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        connect_window = self.main_window.mscolab.connect_window
        self._login(qtbot, self.userdata[0], self.userdata[2])
        mockbox.assert_called_once_with(
            connect_window,
            "Update Credentials",
            "You are using new credentials. Should your settings file be updated with the new credentials?",
            mock.ANY,
            mock.ANY,
        )
        # show logged in widgets
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        assert self.main_window.connectBtn.isVisible() is False
        assert self.main_window.mscolab.connect_window is None
        assert self.main_window.local_active is True
        # test operation listing visibility
        assert self.main_window.listOperationsMSC.model().rowCount() == 1

    def test_logout_action_trigger(self, qtbot):
        # Login
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, self.userdata[0], self.userdata[2])
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        # Logout
        self.main_window.mscolab.logout_action.trigger()
        assert self.main_window.listOperationsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None
        assert self.main_window.local_active is True
        assert self.main_window.usernameLabel.text() == "User"

    def test_logout(self, qtbot):
        # Login
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, self.userdata[0], self.userdata[2])
        assert self.main_window.usernameLabel.text() == self.userdata[1]
        # Logout
        self.main_window.mscolab.logout()
        assert self.main_window.usernameLabel.text() == "User"
        assert self.main_window.connectBtn.isVisible() is True
        assert self.main_window.listOperationsMSC.model().rowCount() == 0
        assert self.main_window.mscolab.conn is None
        assert self.main_window.local_active is True

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_add_user(self, mockmessage, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user("something", "something@something.org", "something")
        assert config_loader(dataset="MSS_auth").get(self.url) == "something@something.org"
        assert mslib.utils.auth.get_password_from_keyring("MSCOLAB",
                                                          "something@something.org") == "password from TestKeyring"
        # assert self.window.stackedWidget.currentWidget() == self.window.newuserPage
        assert self.main_window.usernameLabel.text() == 'something'
        assert self.main_window.mscolab.connect_window is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.No)
    def test_add_users_without_updating_credentials_in_config_file(self, mockmessage, qtbot):
        create_msui_settings_file('{"MSS_auth": {"' + self.url + '": "something@something.org"}}')
        read_config_file()
        # check current settings
        assert config_loader(dataset="MSS_auth").get(self.url) == "something@something.org"
        self._connect_to_mscolab(qtbot)
        assert self.window.mscolab_server_url is not None
        self._create_user("anand", "anand@something.org", "anand_pass")
        # check changed settings
        assert mslib.utils.auth.get_password_from_keyring(service_name=self.url,
                                                          username="anand@something.org") == "anand_pass"
        assert config_loader(dataset="MSS_auth").get(self.url) == "something@something.org"
        # check user is logged in
        assert self.main_window.usernameLabel.text() == "anand"

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_add_users_with_updating_credentials_in_config_file(self, mockmessage, qtbot):
        create_msui_settings_file('{"MSS_auth": {"' + self.url + '": "something@something.org"}}')
        mslib.utils.auth.save_password_to_keyring(service_name=self.url,
                                                  username="something@something.org", password="something")
        read_config_file()
        # check current settings
        assert config_loader(dataset="MSS_auth").get(self.url) == "something@something.org"
        self._connect_to_mscolab(qtbot)
        assert self.window.mscolab_server_url is not None
        self._create_user("anand", "anand@something.org", "anand_pass")
        # check changed settings
        assert config_loader(dataset="MSS_auth").get(self.url) == "anand@something.org"
        assert mslib.utils.auth.get_password_from_keyring(service_name=self.url,
                                                          username="anand@something.org") == "anand_pass"
        # check user is logged in
        assert self.main_window.usernameLabel.text() == "anand"

    def _connect_to_mscolab(self, qtbot, password=""):
        self.window.urlCb.setEditText(self.url)
        self.window.httpPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.window.connectBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert not self.window.connectBtn.isVisible()
            assert self.window.disconnectBtn.isVisible()
        qtbot.wait_until(assert_)

    def _login(self, qtbot, emailid="a", password="a"):
        self.window.loginEmailLe.setText(emailid)
        self.window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.window.loginBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert self.main_window.mscolab.connect_window is None
        qtbot.wait_until(assert_)

    def _create_user(self, username, email, password):
        QtTest.QTest.mouseClick(self.window.addUserBtn, QtCore.Qt.LeftButton)
        self.window.newUsernameLe.setText(str(username))
        self.window.newEmailLe.setText(str(email))
        self.window.newPasswordLe.setText(str(password))
        self.window.newConfirmPasswordLe.setText(str(password))
        okWidget = self.window.newUserBb.button(self.window.newUserBb.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)


class Test_Mscolab:
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
    # import/export plugins
    import_plugins = {
        "TXT": ["txt", "mslib.plugins.io.text", "load_from_txt"],
        "FliteStar": ["txt", "mslib.plugins.io.flitestar", "load_from_flitestar"],
    }
    export_plugins = {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
    }

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mscolab_app, mscolab_server):
        self.app = mscolab_app
        self.url = mscolab_server
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

        self.window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.create_new_flight_track()
        self.window.show()

        self.total_created_operations = 0
        yield
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

    def test_activate_operation(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        # activate a operation
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_name == self.operation_name

    def test_view_open(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        # test after activating operation
        self._activate_operation_at_index(0)
        self.window.actionTableView.trigger()
        assert len(self.window.get_active_views()) == 1
        self.window.actionTopView.trigger()
        assert len(self.window.get_active_views()) == 2
        self.window.actionSideView.trigger()
        assert len(self.window.get_active_views()) == 3
        self.window.actionLinearView.trigger()
        assert len(self.window.get_active_views()) == 4

        operation = self.window.mscolab.active_op_id
        uid = self.window.mscolab.user["id"]
        active_windows = self.window.get_active_views()
        topview = active_windows[1]
        tableview = active_windows[0]
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
            self.window.mscolab.handle_update_permission(operation, uid, "viewer")
            m.assert_called_once()
        assert not tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and not action.isEnabled() for action in topview.mpl.navbar.actions())
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
            self.window.mscolab.handle_update_permission(operation, uid, "creator")
            m.assert_called_once()
        assert tableview.btAddWayPointToFlightTrack.isEnabled()
        assert any(action.text() == "Ins WP" and action.isEnabled() for action in topview.mpl.navbar.actions())

    def test_multiple_views_and_multiple_flightpath(self, qtbot):
        """
        checks that we can have multiple topviews with the multiple flightpath dockingwidget
        and we are able to cycle a login/logout
        """
        # more operations for the user
        for op_name in ["second", "third"]:
            assert add_operation(op_name, "description")
            assert add_user_to_operation(path=op_name, emailid=self.userdata[0])

        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])

        # test after activating operation
        self._activate_operation_at_index(0)
        self.window.actionTopView.trigger()

        def assert_active_views():
            # check 1 view opened
            assert len(self.window.get_active_views()) == 1
        qtbot.wait_until(assert_active_views)
        topview_0 = self.window.listViews.item(0)

        # next topview
        self.window.actionTopView.trigger()
        topview_1 = self.window.listViews.item(1)

        def assert_active_views():
            # check 2 view opened
            assert len(self.window.get_active_views()) == 2
        qtbot.wait_until(assert_active_views)

        # open multiple flightpath first window
        topview_0.window.cbTools.currentIndexChanged.emit(6)

        def assert_dock_loaded():
            assert topview_0.window.docks[5] is not None
        qtbot.wait_until(assert_dock_loaded)

        # activate all operation, this enables them in the docking widget too
        self._activate_operation_at_index(1)
        self._activate_operation_at_index(2)
        self._activate_operation_at_index(0)
        # ToDo refactor to be able to activate/deactivate by the docking widget and that it can be checked

        # open multiple flightpath second window
        topview_1.window.cbTools.currentIndexChanged.emit(6)

        def assert_dock_loaded():
            assert topview_1.window.docks[5] is not None
        qtbot.wait_until(assert_dock_loaded)

        # activate all operation, this enables them in the docking widget too
        self._activate_operation_at_index(1)
        self._activate_operation_at_index(2)
        self._activate_operation_at_index(0)
        # ToDo refactor to be able to activate/deactivate by the docking widget and that it can be checked

        def assert_label_text():
            # verify logged in
            assert self.window.usernameLabel.text() == self.userdata[1]
        qtbot.wait_until(assert_label_text)

        self.window.mscolab.logout()

        def assert_logout_text():
            assert self.window.usernameLabel.text() == "User"
        qtbot.wait_until(assert_logout_text)

        self._connect_to_mscolab(qtbot)
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        # verify logged in again
        qtbot.wait_until(assert_label_text)
        # ToDo verify all operations disabled again without a visual check

    def test_marked_bold_only_in_multiple_flight_path_operations_for_active_operation(self, qtbot):
        """
        checks that when we use operations only the operations is bold marked not the flighttrack too
        """
        # more operations for the user
        for op_name in ["second", "third"]:
            assert add_operation(op_name, "description")
            assert add_user_to_operation(path=op_name, emailid=self.userdata[0])

        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])

        # test after activating operation
        self._activate_operation_at_index(0)
        self.window.actionTopView.trigger()

        def assert_active_views():
            # check 1 view opened
            assert len(self.window.get_active_views()) == 1
        qtbot.wait_until(assert_active_views)

        topview_0 = self.window.listViews.item(0)
        assert topview_0.window.tv_window_exists is True
        # open multiple flightpath first window
        topview_0.window.cbTools.currentIndexChanged.emit(6)

        def assert_dock_loaded():
            assert topview_0.window.docks[5] is not None
        qtbot.wait_until(assert_dock_loaded)
        assert topview_0.window.active_op_id is not None

        list_flighttrack = topview_0.window.docks[5].widget().list_flighttrack
        list_operation_track = topview_0.window.docks[5].widget().list_operation_track

        for i in range(list_operation_track.count()):
            listItem = list_operation_track.item(i)
            if self.window.mscolab.active_op_id == listItem.op_id:
                assert listItem.font().bold() is True
        for i in range(list_flighttrack.count()):
            listItem = list_flighttrack.item(i)
            assert listItem.font().bold() is False

    def test_correct_active_op_id_in_topview(self, qtbot):
        """
        checks that active_op_id is set
        """
        # more operations for the user
        for op_name in ["second", "third"]:
            assert add_operation(op_name, "description")
            assert add_user_to_operation(path=op_name, emailid=self.userdata[0])

        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])

        assert self.window.mscolab.active_op_id is None
        # test after activating operation
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        selected_op_id = self.window.mscolab.active_op_id
        self.window.actionTopView.trigger()

        def assert_active_views():
            # check 1 view opened
            assert len(self.window.get_active_views()) == 1
        qtbot.wait_until(assert_active_views)
        topview_0 = self.window.listViews.item(0)
        assert topview_0.window.active_op_id is not None
        assert topview_0.window.active_op_id == selected_op_id

    def test_multiple_flightpath_switching_to_flighttrack_and_logout(self, qtbot):
        """
        checks that we can switch in topviews with the multiple flightpath dockingwidget
        between local flight track and operations, and we are able to cycle a login/logout
        """
        # more operations for the user
        for op_name in ["second", "third"]:
            assert add_operation(op_name, "description")
            assert add_user_to_operation(path=op_name, emailid=self.userdata[0])

        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])

        # test after activating operation
        self._activate_operation_at_index(0)
        self.window.actionTopView.trigger()

        def assert_active_views():
            # check 1 view opened
            assert len(self.window.get_active_views()) == 1
        qtbot.wait_until(assert_active_views)
        topview_0 = self.window.listViews.item(0)
        assert topview_0.window.tv_window_exists is True
        topview_0.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        def assert_attribute():
            assert topview_0.window.testAttribute(QtCore.Qt.WA_DeleteOnClose)
        qtbot.wait_until(assert_attribute)

        # open multiple flightpath first window
        topview_0.window.cbTools.currentIndexChanged.emit(6)

        def assert_dock_loaded():
            assert topview_0.window.docks[5] is not None
        qtbot.wait_until(assert_dock_loaded)

        # activate all operation, this enables them in the docking widget too
        self._activate_operation_at_index(1)
        self._activate_operation_at_index(2)
        self._activate_operation_at_index(0)
        # ToDo refactor to be able to activate/deactivate by the docking widget and that it can be checked

        self._activate_flight_track_at_index(0)
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            topview_0.window.close()

        def assert_window_closed():
            assert topview_0.window.tv_window_exists is False
        qtbot.wait_until(assert_window_closed)

        def assert_label_text():
            # verify logged in
            assert self.window.usernameLabel.text() == self.userdata[1]
        qtbot.wait_until(assert_label_text)

        self.window.mscolab.logout()

        def assert_logout_text():
            assert self.window.usernameLabel.text() == "User"
        qtbot.wait_until(assert_logout_text)

        self._connect_to_mscolab(qtbot)
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        # verify logged in again
        qtbot.wait_until(assert_label_text)
        # ToDo verify all operations disabled again without a visual check

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'),
                              "Flight track (*.ftml)"))
    def test_handle_export(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        self._activate_operation_at_index(0)
        self.window.actionExportFlightTrackFTML.trigger()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.mscolab.data_dir,
                                                                       'test_export.ftml'))
        wp_count = len(self.window.mscolab.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.mscolab.waypoints_model.waypoint_data(i).lat

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="This test is flaky on macOS because of some cleanup error in temporary files.",
    )
    @pytest.mark.parametrize("name", [("example.ftml", "actionImportFlightTrackFTML", 5),
                                      ("example.csv", "actionImportFlightTrackCSV", 5),
                                      ("example.txt", "actionImportFlightTrackTXT", 5),
                                      ("flitestar.txt", "actionImportFlightTrackFliteStar", 10)])
    def test_import_file(self, name, qtbot):
        self.window.remove_plugins()
        with mock.patch("mslib.msui.msui_mainwindow.config_loader", return_value=self.import_plugins):
            self.window.add_import_plugins("qt")
        file_path = fs.path.join(self.sample_path, name[0])
        with mock.patch("mslib.msui.msui_mainwindow.get_open_filenames", return_value=[file_path]) as mockopen:
            self._connect_to_mscolab(qtbot)
            modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
            self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
            self._activate_operation_at_index(0)
            wp = self.window.mscolab.waypoints_model
            assert len(wp.waypoints) == 2
            for action in self.window.menuImportFlightTrack.actions():
                if action.objectName() == name[1]:
                    with mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
                        action.trigger()
                        m.assert_called_once()
                    break
            assert mockopen.call_count == 1
            imported_wp = self.window.mscolab.waypoints_model
            assert len(imported_wp.waypoints) == name[2]

    def test_none_import_file(self, qtbot):
        with mock.patch("mslib.msui.msui_mainwindow.get_open_filenames", return_value=None) as mockopen:
            self._connect_to_mscolab(qtbot)
            modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
            self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
            self._activate_operation_at_index(0)
            wp = self.window.mscolab.waypoints_model
            assert len(wp.waypoints) == 2
            for action in self.window.menuImportFlightTrack.actions():
                if action.objectName() == "actionImportFlightTrackFTML":
                    action.trigger()
                    break
            assert mockopen.call_count == 1
            imported_wp = self.window.mscolab.waypoints_model
            assert len(imported_wp.waypoints) == 2

    def test_work_locally_toggle(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(qtbot, emailid=self.userdata[0], password=self.userdata[2])
        self._activate_operation_at_index(0)
        self.window.workLocallyCheckbox.setChecked(True)
        self.window.mscolab.waypoints_model.invert_direction()
        wpdata_local = self.window.mscolab.waypoints_model.waypoint_data(0)
        self.window.workLocallyCheckbox.setChecked(False)
        wpdata_server = self.window.mscolab.waypoints_model.waypoint_data(0)
        assert wpdata_local.lat != wpdata_server.lat

    @mock.patch("mslib.msui.mscolab.get_open_filename", return_value=os.path.join(sample_path, u"example.ftml"))
    def test_browse_add_operation(self, mockopen, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self.window.actionAddOperation.trigger()
        self.window.mscolab.add_proj_dialog.path.setText(str("example"))
        self.window.mscolab.add_proj_dialog.description.setText(str("example"))
        self.window.mscolab.add_proj_dialog.category.setText(str("example"))
        QtTest.QTest.mouseClick(self.window.mscolab.add_proj_dialog.browse, QtCore.Qt.LeftButton)
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
            QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)

            def assert_():
                m.assert_called_once()
            qtbot.wait_until(assert_)

        def assert_():
            assert self.window.listOperationsMSC.model().rowCount() == 1
            item = self.window.listOperationsMSC.item(0)
            assert item.operation_path == "example"
            assert item.access_level == "creator"
        qtbot.wait_until(assert_)

    def test_add_operation(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "Alpha", "Description Alpha")
        with (mock.patch("PyQt5.QtWidgets.QLineEdit.text", return_value=None),
              mock.patch("PyQt5.QtWidgets.QErrorMessage.showMessage") as m):
            self._create_operation_unchecked("Alpha2", "Description Alpha")
            m.assert_called_once_with("Path can't be empty")
        with (mock.patch("PyQt5.QtWidgets.QTextEdit.toPlainText", return_value=None),
              mock.patch("PyQt5.QtWidgets.QErrorMessage.showMessage") as m):
            self._create_operation_unchecked("Alpha3", "Description Alpha")
            m.assert_called_once_with("Description can't be empty")
        with mock.patch("PyQt5.QtWidgets.QErrorMessage.showMessage") as m:
            self._create_operation_unchecked("/", "Description Alpha")
            m.assert_called_once_with("Path can't contain spaces or special characters")
        self._create_operation(qtbot, "reproduce-test", "Description Test")
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_operation_name == "Alpha"
        self._activate_operation_at_index(1)
        assert self.window.mscolab.active_operation_name == "reproduce-test"

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("flight7", True))
    def test_handle_delete_operation(self, mocktext, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "berta@something.org"}})
        self._create_user(qtbot, "berta", "berta@something.org", "something")
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        operation_name = "flight7"
        self._create_operation(qtbot, operation_name, "Description flight7")
        # check for operation dir is created on server
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name))
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is not None
        assert self.window.listOperationsMSC.model().rowCount() == 1
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok) as m:
            self.window.actionDeleteOperation.trigger()
            qtbot.wait_until(
                lambda: m.assert_called_once_with(self.window, "Success", 'Operation "flight7" was deleted!')
            )
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is None
        # check operation dir name removed
        assert os.path.isdir(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, operation_name)) is False

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_handle_leave_operation(self, mockmessage, qtbot):
        self._connect_to_mscolab(qtbot)

        modify_config_file({"MSS_auth": {self.url: self.userdata3[0]}})
        self._login(qtbot, self.userdata3[0], self.userdata3[2])
        assert self.window.usernameLabel.text() == self.userdata3[1]
        assert self.window.connectBtn.isVisible() is False

        assert self.window.listOperationsMSC.model().rowCount() == 1
        assert self.window.mscolab.active_op_id is None
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        assert op_id is not None

        self.window.actionTopView.trigger()
        assert len(self.window.get_active_views()) == 1
        self.window.actionSideView.trigger()
        assert len(self.window.get_active_views()) == 2

        self.window.actionLeaveOperation.trigger()

        def assert_leave_operation_done():
            assert self.window.mscolab.active_op_id is None
            assert self.window.listViews.count() == 0
            assert self.window.listOperationsMSC.model().rowCount() == 0
        qtbot.wait_until(assert_leave_operation_done)

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("new_name", True))
    def test_handle_rename_operation(self, mocktext, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok) as m:
            self.window.actionRenameOperation.trigger()
            m.assert_called_once_with(self.window, "Rename successful", "Operation is renamed successfully.")
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_name == "new_name"

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("new_description", True))
    def test_update_description(self, mocktext, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok) as m:
            self.window.actionChangeDescription.trigger()
            m.assert_called_once_with(self.window, "Update successful", "Description is updated successfully.")
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_description == "new_description"

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=("new_category", True))
    def test_update_category(self, mocktext, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        assert self.window.mscolab.active_operation_category == "example"
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok) as m:
            self.window.actionChangeCategory.trigger()
            m.assert_called_once_with(self.window, "Update successful", "Category is updated successfully.")
        assert self.window.mscolab.active_op_id is not None
        assert self.window.mscolab.active_operation_category == "new_category"

    def test_any_special_category(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        self._create_operation(qtbot, "flight5678", "Description flight5678", category="furtherexample")
        # all operations of two defined categories are found
        assert self.window.mscolab.selected_category == "*ANY*"
        operation_pathes = [self.window.mscolab.ui.listOperationsMSC.item(i).operation_path for i in
                            range(self.window.mscolab.ui.listOperationsMSC.count())]
        assert ["flight1234", "flight5678"] == operation_pathes
        self.window.mscolab.ui.filterCategoryCb.setCurrentIndex(2)
        # only operation of furtherexample are found
        assert self.window.mscolab.selected_category == "furtherexample"
        operation_pathes = [self.window.mscolab.ui.listOperationsMSC.item(i).operation_path for i in
                            range(self.window.mscolab.ui.listOperationsMSC.count())]
        assert ["flight5678"] == operation_pathes

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok)
    def test_get_recent_op_id(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "anton@something.org"}})
        self._create_user(qtbot, "anton", "anton@something.org", "something")
        assert self.window.usernameLabel.text() == 'anton'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation(qtbot, "flight2", "Description flight2")
        current_op_id = self.window.mscolab.get_recent_op_id()
        self._create_operation(qtbot, "flight3", "Description flight3")
        self._create_operation(qtbot, "flight4", "Description flight4")
        # ToDo fix number after cleanup initial data
        assert self.window.mscolab.get_recent_op_id() == current_op_id + 2

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok)
    def test_get_recent_operation(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "berta@something.org"}})
        self._create_user(qtbot, "berta", "berta@something.org", "something")
        assert self.window.usernameLabel.text() == 'berta'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        self._activate_operation_at_index(0)
        operation = self.window.mscolab.get_recent_operation()
        assert operation["path"] == "flight1234"
        assert operation["access_level"] == "creator"

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok)
    def test_open_chat_window(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        assert self.window.listOperationsMSC.model().rowCount() == 1
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionChat.trigger()
        assert self.window.mscolab.chat_window is not None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok)
    def test_close_chat_window(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self._create_operation(qtbot, "flight1234", "Description flight1234")
        self._activate_operation_at_index(0)
        assert self.window.mscolab.active_op_id is not None
        self.window.actionChat.trigger()
        self.window.mscolab.close_chat_window()
        assert self.window.mscolab.chat_window is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok)
    def test_delete_operation_from_list(self, mockbox, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "other@something.org"}})
        self._create_user(qtbot, "other", "other@something.org", "something")
        assert self.window.usernameLabel.text() == 'other'
        assert self.window.connectBtn.isVisible() is False
        assert self.window.listOperationsMSC.model().rowCount() == 0
        self._create_operation(qtbot, "flight3", "Description flight3")
        self._activate_operation_at_index(0)
        op_id = self.window.mscolab.get_recent_op_id()
        self.window.mscolab.delete_operation_from_list(op_id)
        assert self.window.mscolab.active_op_id is None

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockmessage, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        u_id = self.window.mscolab.user['id']
        self.window.mscolab.open_profile_window()
        QtTest.QTest.mouseClick(self.window.mscolab.profile_dialog.deleteAccountBtn, QtCore.Qt.LeftButton)
        assert self.window.listOperationsMSC.model().rowCount() == 0
        assert self.window.usernameLabel.isVisible() is False
        assert self.window.connectBtn.isVisible() is True
        with self.app.app_context():
            assert User.query.filter_by(emailid='something').count() == 0
            assert Permission.query.filter_by(u_id=u_id).count() == 0

    def test_open_help_dialog(self):
        self.window.actionMSColabHelp.trigger()
        assert self.window.mscolab.help_dialog is not None

    def test_close_help_dialog(self, qtbot):
        self.window.actionMSColabHelp.trigger()
        assert self.window.mscolab.help_dialog is not None
        QtTest.QTest.mouseClick(
            self.window.mscolab.help_dialog.okayBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert self.window.mscolab.help_dialog is None
        qtbot.wait_until(assert_)

    def test_create_dir_exceptions(self):
        with mock.patch("fs.open_fs", new=ExceptionMock(fs.errors.CreateFailed).raise_exc), \
                mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critbox, \
                mock.patch("sys.exit") as mockexit:
            self.window.mscolab.data_dir = "://"
            self.window.mscolab.create_dir()
            critbox.assert_called_once()
            mockexit.assert_called_once()

        with mock.patch("fs.open_fs", new=ExceptionMock(fs.opener.errors.UnsupportedProtocol).raise_exc), \
                mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critbox, \
                mock.patch("sys.exit") as mockexit:
            self.window.mscolab.data_dir = "://"
            self.window.mscolab.create_dir()
            critbox.assert_called_once()
            mockexit.assert_called_once()

    def test_profile_dialog(self, qtbot):
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: "something@something.org"}})
        self._create_user(qtbot, "something", "something@something.org", "something")
        self.window.mscolab.profile_action.trigger()
        # case: default gravatar is set and no messagebox is called
        assert self.window.mscolab.prof_diag is not None
        # case: trying to fetch non-existing gravatar
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critbox:
            self.window.mscolab.fetch_gravatar(refresh=True)
            critbox.assert_called_once()
        assert not self.window.mscolab.profile_dialog.gravatarLabel.pixmap().isNull()

    def _connect_to_mscolab(self, qtbot):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert not self.connect_window.connectBtn.isVisible()
            assert self.connect_window.disconnectBtn.isVisible()
        qtbot.wait_until(assert_)

    def _login(self, qtbot, emailid, password):
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert self.window.mscolab.connect_window is None
        qtbot.wait_until(assert_)

    def _create_user(self, qtbot, username, email, password):
        QtTest.QTest.mouseClick(self.connect_window.addUserBtn, QtCore.Qt.LeftButton)
        self.connect_window.newUsernameLe.setText(str(username))
        self.connect_window.newEmailLe.setText(str(email))
        self.connect_window.newPasswordLe.setText(str(password))
        self.connect_window.newConfirmPasswordLe.setText(str(password))
        okWidget = self.connect_window.newUserBb.button(self.connect_window.newUserBb.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)

        def assert_user_created():
            assert self.window.usernameLabel.text() == username
            assert self.window.connectBtn.isVisible() is False
        qtbot.wait_until(assert_user_created)

    def _create_operation_unchecked(self, path, description, category="example"):
        self.window.actionAddOperation.trigger()
        self.window.mscolab.add_proj_dialog.path.setText(str(path))
        self.window.mscolab.add_proj_dialog.description.setText(str(description))
        self.window.mscolab.add_proj_dialog.category.setText(category)
        okWidget = self.window.mscolab.add_proj_dialog.buttonBox.button(
            self.window.mscolab.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)

    def _create_operation(self, qtbot, path, description, category="example"):
        self.total_created_operations = self.total_created_operations + 1
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Ok) as m:
            self._create_operation_unchecked(path, description, category)
            m.assert_called_once_with(
                self.window,
                "Creation successful",
                "Your operation was created successfully.",
            )

        def assert_operation_is_listed():
            assert self.window.listOperationsMSC.model().rowCount() == self.total_created_operations
        qtbot.wait_until(assert_operation_is_listed)

    def _activate_operation_at_index(self, index):
        # The main window must be on top
        self.window.activateWindow()
        # get the item by its index
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)

    def _activate_flight_track_at_index(self, index):
        # The main window must be on top
        self.window.activateWindow()
        # get the item by its index
        item = self.window.listFlightTracks.item(index)
        point = self.window.listFlightTracks.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseDClick(self.window.listFlightTracks.viewport(), QtCore.Qt.LeftButton, pos=point)
