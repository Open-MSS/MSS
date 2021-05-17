# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_admin_window
    ~~~~~~~~~~~~~~~~~~~~~

    Mscolab project window, to display chat, file change

    This file is part of mss.

    :copyright: 2020 Tanish Grover
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
import json

import requests
from werkzeug.urls import url_join

from PyQt5 import QtCore, QtWidgets
from mslib.msui.qt5 import ui_mscolab_admin_window as ui
from mslib.utils import config_loader, show_popup


class MSColabAdminWindow(QtWidgets.QMainWindow, ui.Ui_MscolabAdminWindow):

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, token, p_id, user, project_name, projects, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB")):
        """
        token: access token
        p_id: project id
        conn: connection to send/receive socket messages
        """
        super(MSColabAdminWindow, self).__init__(parent)
        self.setupUi(self)

        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.p_id = p_id
        self.user = user
        self.project_name = project_name
        self.projects = projects
        self.conn = conn

        self.addUsers = []
        self.modifyUsers = []

        # Button click handlers
        self.addUsersBtn.clicked.connect(self.add_selected_users)
        self.modifyUsersBtn.clicked.connect(self.modify_selected_users)
        self.deleteUsersBtn.clicked.connect(self.delete_selected_users)
        self.importPermissionsBtn.clicked.connect(self.import_permissions)
        self.selectAllAddBtn.clicked.connect(lambda: self.select_all(self.addUsersTable))
        self.deselectAllAddBtn.clicked.connect(lambda: self.deselect_all(self.addUsersTable))
        self.selectAllModifyBtn.clicked.connect(lambda: self.select_all(self.modifyUsersTable))
        self.deselectAllModifyBtn.clicked.connect(lambda: self.deselect_all(self.modifyUsersTable))

        # Search filter
        self.addUsersSearch.textChanged.connect(lambda text: self.search_user_filter(text, self.addUsersTable))
        self.modifyUsersSearch.textChanged.connect(lambda text: self.search_user_filter(text, self.modifyUsersTable))
        self.modifyUsersPermissionFilter.currentTextChanged.connect(self.apply_permission_filter)

        # Setting handlers for connection manager
        self.conn.signal_project_permissions_updated.connect(self.handle_permissions_updated)

        self.set_label_text()
        self.load_users_without_permission()
        self.load_users_with_permission()
        self.populate_import_permission_cb()

    def populate_table(self, table, users):
        table.setRowCount(0)
        for row_number, row_data in enumerate(users):
            table.insertRow(row_number)
            for col_number, item in enumerate(row_data):
                new_item = QtWidgets.QTableWidgetItem(item)
                table.setItem(row_number, col_number, new_item)

    def populate_import_permission_cb(self):
        self.importPermissionsCB.clear()
        for project in self.projects:
            if project['p_id'] != self.p_id:
                self.importPermissionsCB.addItem(project['path'], project['p_id'])

    def get_selected_userids(self, table, users):
        u_ids = []
        selected_rows = table.selectionModel().selectedRows()
        for row in selected_rows:
            u_ids.append(users[row.row()][-1])

        return u_ids

    def select_all(self, table):
        table.setFocus()
        for row_num in range(table.rowCount()):
            # Check if row is hidden due to some filter to exclude it
            if table.item(row_num, 0).isSelected() is False and table.isRowHidden(row_num) is False:
                table.selectRow(row_num)

    def deselect_all(self, table):
        table.setFocus()
        for row_num in range(table.rowCount()):
            # Check if row is hidden due to some filter to exclude it
            if table.item(row_num, 0).isSelected() and table.isRowHidden(row_num) is False:
                table.selectRow(row_num)

    # TODO: Think of a more cleaner implementation.
    def apply_filters(self, table, text_filter, permission_filter=None):
        for row_num in range(table.rowCount()):
            if text_filter in table.item(row_num, 0).text():
                if permission_filter:
                    if permission_filter == "all" or permission_filter == table.item(row_num, 1).text():
                        table.showRow(row_num)
                    else:
                        table.hideRow(row_num)
                else:
                    table.showRow(row_num)
            else:
                table.hideRow(row_num)

    def search_user_filter(self, text_filter, table):
        permission_filter = None
        if table == self.modifyUsersTable:
            permission_filter = str(self.modifyUsersPermissionFilter.currentText())
        self.apply_filters(table, text_filter, permission_filter)

    def apply_permission_filter(self, permission_filter):
        self.modifyUsersTable.setFocus()
        text_filter = self.modifyUsersSearch.text()
        self.apply_filters(self.modifyUsersTable, text_filter, permission_filter)

    def set_label_text(self):
        self.projectNameLabel.setText(f"Project: {self.project_name}")
        self.usernameLabel.setText(f"Logged In: {self.user['username']}")

    def load_users_without_permission(self):
        self.addUsers = []
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        url = url_join(self.mscolab_server_url, "users_without_permission")
        res = requests.get(url, data=data)
        res = res.json()
        if res["success"]:
            self.addUsers = res["users"]
            self.populate_table(self.addUsersTable, self.addUsers)
            text_filter = self.addUsersSearch.text()
            self.apply_filters(self.addUsersTable, text_filter, None)
        else:
            show_popup(self, "Error", res["message"])

    def load_users_with_permission(self):
        self.modifyUsers = []
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        url = url_join(self.mscolab_server_url, "users_with_permission")
        res = requests.get(url, data=data)
        res = res.json()
        if res["success"]:
            self.modifyUsers = res["users"]
            self.populate_table(self.modifyUsersTable, self.modifyUsers)
            text_filter = self.modifyUsersSearch.text()
            permission_filter = str(self.modifyUsersPermissionFilter.currentText())
            self.apply_filters(self.modifyUsersTable, text_filter, permission_filter)
        else:
            show_popup(self, "Error", res["message"])

    def add_selected_users(self):
        selected_userids = self.get_selected_userids(self.addUsersTable, self.addUsers)
        if len(selected_userids) == 0:
            return

        selected_access_level = str(self.addUsersPermission.currentText())
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "selected_userids": json.dumps(selected_userids),
            "selected_access_level": selected_access_level
        }
        url = url_join(self.mscolab_server_url, "add_bulk_permissions")
        res = requests.post(url, data=data)
        res = res.json()
        if res["success"]:
            # TODO: Do we need a success popup?
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            show_popup(self, "Error", res["message"])

    def modify_selected_users(self):
        selected_userids = self.get_selected_userids(self.modifyUsersTable, self.modifyUsers)
        if len(selected_userids) == 0:
            return

        selected_access_level = str(self.modifyUsersPermission.currentText())
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "selected_userids": json.dumps(selected_userids),
            "selected_access_level": selected_access_level
        }
        url = url_join(self.mscolab_server_url, "modify_bulk_permissions")
        res = requests.post(url, data=data)
        res = res.json()
        if res["success"]:
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            self.show_error_popup(res["message"])

    def delete_selected_users(self):
        selected_userids = self.get_selected_userids(self.modifyUsersTable, self.modifyUsers)
        if len(selected_userids) == 0:
            return

        data = {
            "token": self.token,
            "p_id": self.p_id,
            "selected_userids": json.dumps(selected_userids)
        }
        url = url_join(self.mscolab_server_url, "delete_bulk_permissions")
        res = requests.post(url, data=data)
        res = res.json()
        if res["success"]:
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            self.show_error_popup(res["message"])

    def import_permissions(self):
        import_p_id = self.importPermissionsCB.currentData(QtCore.Qt.UserRole)
        data = {
            "token": self.token,
            "current_p_id": self.p_id,
            "import_p_id": import_p_id
        }
        url = url_join(self.mscolab_server_url, 'import_permissions')
        res = requests.post(url, data=data).json()
        if res["success"]:
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            show_popup(self, "Error", res["message"])

    # Socket Events
    def handle_permissions_updated(self, u_id):
        if self.user["id"] == u_id:
            return

        show_popup(self, 'Alert', 'The permissions for this project were updated! The window is going to refresh.', 1)
        self.load_users_without_permission()
        self.load_users_with_permission()

    def closeEvent(self, event):
        self.viewCloses.emit()
        event.accept()
