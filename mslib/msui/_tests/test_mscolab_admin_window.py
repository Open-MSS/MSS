# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
import time

from mslib.mscolab.server import db, APP, initialize_managers
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
import mslib.msui.mscolab as mc


class Test_MscolabAdminWindow(object):
    def setup(self):
        # start mscolab server
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)

        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mc.MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                          mscolab_server_url=MSCOLAB_URL_TEST)
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
            self.window.admin_window.hide()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.close()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_filters(self):
        len_unadded_users = self.admin_window.addUsersTable.rowCount()
        len_added_users = self.admin_window.modifyUsersTable. rowCount()

        # Search Filter Add Users Table
        QtTest.QTest.keyClicks(self.admin_window.addUsersSearch, "test2")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.addUsersTable)
        assert visible_row_count == 1
        self.admin_window.addUsersSearch.setText("")
        QtTest.QTest.keyClicks(self.admin_window.addUsersSearch, "")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.addUsersTable)
        assert visible_row_count == len_unadded_users
        # Search Filter Modify Users Table
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "test4")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        self.admin_window.modifyUsersSearch.setText("")
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == len_added_users
        # Permission Filter Modify Filter Table
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("viewer")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("all")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == len_added_users
        # Both Search and permission filter together
        QtTest.QTest.keyClicks(self.admin_window.modifyUsersSearch, "test4")
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("viewer")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 1
        self.admin_window.modifyUsersPermissionFilter.currentTextChanged.emit("admin")
        QtWidgets.QApplication.processEvents()
        visible_row_count = self._get_visible_row_count(self.admin_window.modifyUsersTable)
        assert visible_row_count == 0

    def test_permission_operations(self):
        # Get starting number of users in each table
        len_unadded_users = self.admin_window.addUsersTable.rowCount()
        len_added_users = self.admin_window.modifyUsersTable.rowCount()

        # Select 2 test Users
        self._select_users(self.admin_window.addUsersTable)
        assert len(self.admin_window.addUsersTable.selectionModel().selectedRows()) == 2

        # Add the 2 selected users
        QtTest.QTest.mouseClick(self.admin_window.addUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len_unadded_users - 2 == self.admin_window.addUsersTable.rowCount()
        assert len_added_users + 2 == self.admin_window.modifyUsersTable.rowCount()

        # Select the 2 new added users from the modify table
        self._select_users(self.admin_window.modifyUsersTable)
        assert len(self.admin_window.modifyUsersTable.selectionModel().selectedRows()) == 2

        # Set their permission to viewer
        index = self.admin_window.modifyUsersPermission.findText("viewer", QtCore.Qt.MatchFixedString)
        self.admin_window.modifyUsersPermission.setCurrentIndex(index)
        QtTest.QTest.mouseClick(self.admin_window.modifyUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len_added_users + 2 == self.admin_window.modifyUsersTable.rowCount()

        # Check if their permission has been updated
        for row_num in range(self.admin_window.modifyUsersTable.rowCount()):
            item = self.admin_window.modifyUsersTable.item(row_num, 0)
            username = item.text()
            if username == "test2" or username == "test3":
                assert self.admin_window.modifyUsersTable.item(row_num, 2).text() == "viewer"

        # Select the users from modify table
        self._select_users(self.admin_window.modifyUsersTable)
        assert len(self.admin_window.modifyUsersTable.selectionModel().selectedRows()) == 2

        # Delete the users
        QtTest.QTest.mouseClick(self.admin_window.deleteUsersBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len_unadded_users == self.admin_window.addUsersTable.rowCount()
        assert len_added_users == self.admin_window.modifyUsersTable.rowCount()

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
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

    def _select_users(self, table):
        for row_num in range(table.rowCount()):
            item = table.item(row_num, 0)
            username = item.text()
            if username == "test2" or username == "test3":
                point = table.visualItemRect(item).center()
                QtTest.QTest.mouseClick(table.viewport(), QtCore.Qt.LeftButton, pos=point)
                QtWidgets.QApplication.processEvents()

    def _get_visible_row_count(self, table):
        visible_row_count = 0
        for row_num in range(table.rowCount()):
            if table.isRowHidden(row_num) is False:
                visible_row_count += 1
        return visible_row_count
