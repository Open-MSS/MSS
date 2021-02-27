# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_admin_window
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
import pytest
import sys
import time

from mslib.msui.mscolab import MSSMscolabWindow
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, db, initialize_managers
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.mscolab.mscolab import handle_db_seed


@pytest.mark.usefixtures("start_mscolab_server")
@pytest.mark.usefixtures("stop_server")
@pytest.mark.usefixtures("create_data")
class Test_MscolabAdminWindow(object):
    def setup(self):
        """
        User being used during test: id = 5, username = test1
        """
        handle_db_seed()
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.url = self.app.config['URL']
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self._login()
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.adminWindowBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.admin_window = self.window.admin_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        # to disconnect connections, and clear token
        # Not logging out since it pops up a dialog
        # self.window.logout()
        if self.window.admin_window:
            self.window.admin_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.close()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_permission_filter(self):
        len_added_users = self.admin_window.modifyUsersTable.rowCount()
        # Change filter to viewer
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("viewer")
        QtWidgets.QApplication.processEvents()
        # Check how many users are visible
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        # Change it back to all
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("all")
        QtWidgets.QApplication.processEvents()
        # Check how many rows are visible
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == len_added_users

    def test_text_search_filter(self):
        len_unadded_users = self.admin_window.addUsersTable.rowCount()
        len_added_users = self.admin_window.modifyUsersTable.rowCount()
        # Text Search in add users Table
        QtTest.QTest.keyClicks(self.admin_window.addUsersSearch, "test2")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.addUsersTable)
        assert visible_row_count == 1
        self.admin_window.addUsersSearch.setText("")
        QtTest.QTest.keyClicks(self.admin_window.addUsersSearch, "")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.addUsersTable)
        assert visible_row_count == len_unadded_users
        # Text Search in modify users Table
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "test4")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        self.admin_window.modifyUsersSearch.setText("")
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == len_added_users

    def test_permission_and_text_together(self):
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "test4")
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("viewer")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("admin")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 0

    def test_add_permissions(self):
        len_unadded_users = self.admin_window.addUsersTable.rowCount()
        len_added_users = self.admin_window.modifyUsersTable.rowCount()
        users = ["test2", "test3"]
        # Select users in the add users table
        self._select_users(self.admin_window.addUsersTable, users)
        QtTest.QTest.mouseClick(self.admin_window.addUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # Check if they have been added in the modify users table
        self._check_users_present(self.admin_window.modifyUsersTable, users, "admin")
        assert len_unadded_users - 2 == self.admin_window.addUsersTable.rowCount()
        assert len_added_users + 2 == self.admin_window.modifyUsersTable.rowCount()

    def test_modify_permissions(self):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        users = ["test2", "test3"]
        # Select users in the add users table
        self._select_users(self.admin_window.addUsersTable, users)
        QtTest.QTest.mouseClick(self.admin_window.addUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # Select users in the modify users table
        self._select_users(self.admin_window.modifyUsersTable, users)
        # Update their permission to viewer
        index = self.admin_window.modifyUsersPermission.findText("viewer", QtCore.Qt.MatchFixedString)
        self.admin_window.modifyUsersPermission.setCurrentIndex(index)
        QtTest.QTest.mouseClick(self.admin_window.modifyUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # Check if the permission has been updated
        self._check_users_present(self.admin_window.modifyUsersTable, users, "viewer")

    def test_delete_permissions(self):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        # Select users in the add users table
        users = ["test2", "test3"]
        self._select_users(self.admin_window.addUsersTable, users)
        QtTest.QTest.mouseClick(self.admin_window.addUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        len_unadded_users = self.admin_window.addUsersTable.rowCount()
        len_added_users = self.admin_window.modifyUsersTable.rowCount()

        # Select users in the modify users table
        self._select_users(self.admin_window.modifyUsersTable, users)
        # Click on delete permissions
        QtTest.QTest.mouseClick(self.admin_window.deleteUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # Check if the deleted users can be found in the add users table
        self._check_users_present(self.admin_window.addUsersTable, users)
        assert len_unadded_users + 2 == self.admin_window.addUsersTable.rowCount()
        assert len_added_users - 2 == self.admin_window.modifyUsersTable.rowCount()

    def test_import_permissions(self):
        self._connect_to_mscolab()
        self._login()
        self._activate_project_at_index(0)
        index = self.admin_window.importPermissionsCB.findText("three", QtCore.Qt.MatchFixedString)
        self.admin_window.importPermissionsCB.setCurrentIndex(index)
        QtTest.QTest.mouseClick(self.admin_window.importPermissionsBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(1)
        assert self.admin_window.modifyUsersTable.rowCount() == 5

    def _connect_to_mscolab(self):
        self.window.url.setEditText(self.url)
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self):
        # login
        self._connect_to_mscolab()
        self.window.emailid.setText('test1')
        self.window.password.setText('test1')
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _select_users(self, table, users):
        for row_num in range(table.rowCount()):
            item = table.item(row_num, 0)
            username = item.text()
            if username in users:
                point = table.visualItemRect(item).center()
                QtTest.QTest.mouseClick(table.viewport(), QtCore.Qt.LeftButton, pos=point)
                QtWidgets.QApplication.processEvents()
        assert len(table.selectionModel().selectedRows()) == 2

    def _get_visible_row_count(self, table):
        visible_row_count = 0
        for row_num in range(table.rowCount()):
            if table.isRowHidden(row_num) is False:
                visible_row_count += 1
        return visible_row_count

    def _check_users_present(self, table, users, access_level=None):
        found = 0
        for row_num in range(table.rowCount()):
            item = table.item(row_num, 0)
            username = item.text()
            if username in users:
                found += 1
                if access_level is not None:
                    assert table.item(row_num, 2).text() == access_level
        assert found == 2
