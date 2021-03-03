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
import os
import fs
import mock
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Permission, User
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.flighttrack import WaypointsTableModel
from mslib.msui.mscolab import MSSMscolabWindow
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.mscolab.mscolab import handle_db_seed
from mslib._tests.utils import mscolab_delete_all_projects, mscolab_delete_user


class Test_Mscolab(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")

    def setup(self):
        handle_db_seed()
        self.port = 8084
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app, sockio, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        self.MSCOLAB_URL_TEST = f"http://localhost:{self.port}"
        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.MSCOLAB_URL_TEST)

    def teardown(self):
        QtTest.QTest.mouseClick(self.window.logoutButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        with self.app.app_context():
            email = [("something@something.org", "something"),
                     ("other@something.org", "other"),
                     ("anton@something.org", "anton"),
                     ("berta@something.org", "berta"),
                    ]
            for em, username in email:
                mscolab_delete_all_projects(self.app, self.MSCOLAB_URL_TEST, em, "something", username)
                mscolab_delete_user(self.app, self.MSCOLAB_URL_TEST, em, "something")

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
        assert self.window.label.text() == 'Welcome, a'
        assert self.window.loginWidget.isVisible() is False
        # test project listing visibility
        assert self.window.listProjects.model().rowCount() == 3
        # test logout
        QtTest.QTest.mouseClick(self.window.logoutButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjects.model().rowCount() == 0
        # ToDo understand why this is not cleared
        # assert self.window.label.text() == ""
        assert self.window.conn is None

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

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_export.ftml'), None))
    def test_handle_export(self, mockbox):
        self._login()
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.exportBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        exported_waypoints = WaypointsTableModel(filename=fs.path.join(self.window.data_dir, 'test_export.ftml'))
        wp_count = len(self.window.waypoints_model.waypoints)
        assert wp_count == 2
        for i in range(wp_count):
            assert exported_waypoints.waypoint_data(i).lat == self.window.waypoints_model.waypoint_data(i).lat

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_import.ftml'), None))
    @mock.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName",
                return_value=(fs.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_import.ftml'), None))
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_import_file(self, mockExport, mockImport, mockMessage):
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

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockmessage):
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

    def test_add_project_handler(self):
        pass

    def test_check_an_enable_project_accept(self):
        pass

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    @mock.patch("mslib.msui.mscolab.get_open_filename", return_value=os.path.join(sample_path, u"example.ftml"))
    def test_set_exported_file(self, mockopen, mockmessage):
        # name is misleading
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        assert self.window.listProjects.model().rowCount() == 0
        QtTest.QTest.mouseClick(self.window.addProject, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.add_proj_dialog.path.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        self.window.add_proj_dialog.description.setText(str("example"))
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.add_proj_dialog.browse, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.add_proj_dialog.buttonBox.button(self.window.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjects.model().rowCount() == 1

    def test_add_project(self):
        # ToDo testneeds to be independent from test_user_delete
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        assert self.window.label.text() == 'Welcome, something'
        assert self.window.loginWidget.isVisible() is False
        self._create_project("Alpha", "Description Alpha")
        assert self.window.listProjects.model().rowCount() == 1

    def test_add_user_handler(self):
        pass

    def test_add_user(self):
        self._connect_to_mscolab()
        self._create_user("something", "something@something.org", "something")
        self._login("something@something.org", "something")
        # screen shows logout button
        assert self.window.label.text() == 'Welcome, something'
        assert self.window.loginWidget.isVisible() is False

    def test_close_help_dialog(self):
        QtTest.QTest.mouseClick(self.window.helpBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.close()
        assert self.window.help_dialog is None

    def test_open_help_dialog(self):
        QtTest.QTest.mouseClick(self.window.helpBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.help_dialog is not None

    @mock.patch("mslib.msui.mscolab.QtWidgets.QInputDialog.getText", return_value=("flight7", True))
    def test_handle_delete_project(self, mocktext):
        pytest.skip('needs a review for the delete button pressed. Seems to delete a None project')
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        self._login("berta@something.org", "something")
        assert self.window.label.text() == 'Welcome, berta'
        assert self.window.loginWidget.isVisible() is False
        assert self.window.listProjects.model().rowCount() == 0
        self._create_project("flight7", "Description flight7")
        self._activate_project_at_index(0)
        assert self.window.listProjects.model().rowCount() == 1
        QtTest.QTest.mouseClick(self.window.deleteProjectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listProjects.model().rowCount() == 0
        assert self.window.active_pid is None

    def test_close_chat_window(self):
        pass

    def test_open_admin_window(self):
        pass

    def test_authorize(self):
        pass

    def test_get_recent_pid(self):
        self._connect_to_mscolab()
        self._create_user("anton", "anton@something.org", "something")
        self._login("anton@something.org", "something")
        assert self.window.label.text() == 'Welcome, anton'
        assert self.window.loginWidget.isVisible() is False
        assert self.window.listProjects.model().rowCount() == 0
        self._create_project("flight2", "Description flight2")
        current_pid = self.window.get_recent_pid()
        self._create_project("flight3", "Description flight3")
        self._create_project("flight4", "Description flight4")
        # ToDo fix number after cleanup initial data
        assert self.window.get_recent_pid() == current_pid + 2

    def test_get_recent_project(self):
        self._connect_to_mscolab()
        self._create_user("berta", "berta@something.org", "something")
        self._login("berta@something.org", "something")
        assert self.window.label.text() == 'Welcome, berta'
        assert self.window.loginWidget.isVisible() is False
        assert self.window.listProjects.model().rowCount() == 0
        self._create_project("flight1234", "Description flight1234")
        self._activate_project_at_index(0)
        project = self.window.get_recent_project()
        assert project["path"] == "flight1234"
        assert project["access_level"] == "creator"

    def test_disable_navbar_action_buttons(self):
        pass

    def test_enable_navbar_action_buttons(self):
        pass

    def test_save_wp_mscolab(self):
        pass

    def test_reload_view_windows(self):
        pass

    def test_wp_mscolab(self):
        pass

    def test_handle_update_permissions(self):
        pass

    def test_delete_project_from_list(self):
        self._connect_to_mscolab()
        self._create_user("other", "other@something.org", "something")
        self._login("other@something.org", "something")
        assert self.window.label.text() == 'Welcome, other'
        assert self.window.loginWidget.isVisible() is False
        assert self.window.listProjects.model().rowCount() == 0
        self._create_project("flight3", "Description flight3")
        self._activate_project_at_index(0)
        p_id = self.window.get_recent_pid()
        self.window.delete_project_from_list(p_id)
        assert self.window.active_pid is None

    def test_handle_revoke_permissions(self):
        pass

    def test_render_new_permissions(self):
        pass

    def test_handle_project_deleted(self):
        pass

    def test_handle_view(self):
        pass

    def test_setIdentifier(self):
        pass

    def _connect_to_mscolab(self):
        self.window.url.setEditText(self.MSCOLAB_URL_TEST)
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self, emailid="a", password="a"):
        self._connect_to_mscolab()
        self.window.emailid.setText(emailid)
        self.window.password.setText(password)
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    def _create_user(self, username, email, password, mockbox):
        QtTest.QTest.mouseClick(self.window.addUser, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.add_user_dialog.username.setText(str(username))
        QtWidgets.QApplication.processEvents()
        self.window.add_user_dialog.emailid.setText(str(email))
        QtWidgets.QApplication.processEvents()
        self.window.add_user_dialog.password.setText(str(password))
        QtWidgets.QApplication.processEvents()
        self.window.add_user_dialog.rePassword.setText(str(password))
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.add_user_dialog.buttonBox.button(self.window.add_user_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # ToDo get rid of that QMessageBox

    @mock.patch("mslib.msui.mscolab.QtWidgets.QErrorMessage.showMessage")
    def _create_project(self, path, description, mockbox):
        QtTest.QTest.mouseClick(self.window.addProject, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.window.add_proj_dialog.path.setText(str(path))
        QtWidgets.QApplication.processEvents()
        self.window.add_proj_dialog.description.setText(str(description))
        QtWidgets.QApplication.processEvents()
        okWidget = self.window.add_proj_dialog.buttonBox.button(self.window.add_proj_dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()


class Test_MscolabMergeWaypointsDialog(object):
    def setup(self):
        pass

    def teardown(self):
        pass

    def test_handle_selection(self):
        pass

    def test_save_waypoints(self):
        pass

    def test_get_values(self):
        pass


class Test_MSCOLAB_AuthenticationDialog(object):
    def setup(self):
        pass

    def teardown(self):
        pass

    def test_getAuthInfo(self):
        pass


class Test_MscolabHelpDialog(object):
    def setup(self):
        pass

    def teardown(self):
        pass

    def test_closeEvent(self):
        pass
