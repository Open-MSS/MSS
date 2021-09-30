# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_admin_window
    ~~~~~~~~~~~~~~~~~~~~~

    Mscolab operation window, to display chat, file change

    This file is part of mss.

    :copyright: 2020 Tanish Grover
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
from mslib.mscolab.utils import verify_user_token
from mslib.msui.qt5 import ui_mscolab_admin_window as ui
from mslib.msui.mss_qt import show_popup
from mslib.utils.config import config_loader


class MSColabAdminWindow(QtWidgets.QMainWindow, ui.Ui_MscolabAdminWindow):

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, token, op_id, user, operation_name, operations, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB")):
        """
        token: access token
        op_id: operation id
        conn: connection to send/receive socket messages
        """
        super(MSColabAdminWindow, self).__init__(parent)
        self.setupUi(self)

        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.op_id = op_id
        self.user = user
        self.operation_name = operation_name
        self.operations = operations
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

        index = self.addUsersPermission.findText("collaborator", QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.addUsersPermission.setCurrentIndex(index)
        # Search filter
        self.addUsersSearch.textChanged.connect(lambda text: self.search_user_filter(text, self.addUsersTable))
        self.modifyUsersSearch.textChanged.connect(lambda text: self.search_user_filter(text, self.modifyUsersTable))
        self.modifyUsersPermissionFilter.currentTextChanged.connect(self.apply_permission_filter)

        # Setting handlers for connection manager
        self.conn.signal_operation_permissions_updated.connect(self.handle_permissions_updated)

        self.set_label_text()
        self.load_users_without_permission()
        self.load_users_with_permission()
        self.populate_import_permission_cb()

    def populate_table(self, table, users):
        users.sort()
        table.setRowCount(0)
        for row_number, row_data in enumerate(users):
            table.insertRow(row_number)
            for col_number, item in enumerate(row_data):
                new_item = QtWidgets.QTableWidgetItem(item)
                table.setItem(row_number, col_number, new_item)

    def populate_import_permission_cb(self):
        self.importPermissionsCB.clear()
        for operation in self.operations:
            if operation['op_id'] != self.op_id:
                self.importPermissionsCB.addItem(operation['path'], operation['op_id'])

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

    def apply_filters(self, table, text_filter, permission_filter=None):
        # Check if no permission or permission is all
        all_items = permission_filter is None or permission_filter == "all"

        # Show/Hide item based on permission and text_filter
        for row_num in range(table.rowCount()):
            permitted = True if all_items else permission_filter == table.item(row_num, 1).text()
            if permitted and text_filter in table.item(row_num, 0).text():
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
        self.operationNameLabel.setText(f"Operation: {self.operation_name}")
        self.usernameLabel.setText(f"Logged In: {self.user['username']}")

    def load_users_without_permission(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            self.addUsers = []
            data = {
                "token": self.token,
                "op_id": self.op_id
            }
            url = url_join(self.mscolab_server_url, "users_without_permission")
            res = requests.get(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.addUsers = res["users"]
                    self.populate_table(self.addUsersTable, self.addUsers)
                    text_filter = self.addUsersSearch.text()
                    self.apply_filters(self.addUsersTable, text_filter, None)
                else:
                    show_popup(self, "Error", res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def load_users_with_permission(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            self.modifyUsers = []
            data = {
                "token": self.token,
                "op_id": self.op_id
            }
            url = url_join(self.mscolab_server_url, "users_with_permission")
            res = requests.get(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.modifyUsers = res["users"]
                    self.populate_table(self.modifyUsersTable, self.modifyUsers)
                    text_filter = self.modifyUsersSearch.text()
                    permission_filter = str(self.modifyUsersPermissionFilter.currentText())
                    self.apply_filters(self.modifyUsersTable, text_filter, permission_filter)
                else:
                    show_popup(self, "Error", res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def add_selected_users(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            selected_userids = self.get_selected_userids(self.addUsersTable, self.addUsers)
            if len(selected_userids) == 0:
                return

            selected_access_level = str(self.addUsersPermission.currentText())
            data = {
                "token": self.token,
                "op_id": self.op_id,
                "selected_userids": json.dumps(selected_userids),
                "selected_access_level": selected_access_level
            }
            url = url_join(self.mscolab_server_url, "add_bulk_permissions")
            res = requests.post(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    # TODO: Do we need a success popup?
                    self.load_users_without_permission()
                    self.load_users_with_permission()
                else:
                    show_popup(self, "Error", res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def modify_selected_users(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            selected_userids = self.get_selected_userids(self.modifyUsersTable, self.modifyUsers)
            if len(selected_userids) == 0:
                return

            selected_access_level = str(self.modifyUsersPermission.currentText())
            data = {
                "token": self.token,
                "op_id": self.op_id,
                "selected_userids": json.dumps(selected_userids),
                "selected_access_level": selected_access_level
            }
            url = url_join(self.mscolab_server_url, "modify_bulk_permissions")
            res = requests.post(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.load_users_without_permission()
                    self.load_users_with_permission()
                else:
                    self.show_error_popup(res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def delete_selected_users(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            selected_userids = self.get_selected_userids(self.modifyUsersTable, self.modifyUsers)
            if len(selected_userids) == 0:
                return

            data = {
                "token": self.token,
                "op_id": self.op_id,
                "selected_userids": json.dumps(selected_userids)
            }
            url = url_join(self.mscolab_server_url, "delete_bulk_permissions")
            res = requests.post(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.load_users_without_permission()
                    self.load_users_with_permission()
                else:
                    self.show_error_popup(res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def import_permissions(self):
        if verify_user_token(self.mscolab_server_url, self.token):
            import_op_id = self.importPermissionsCB.currentData(QtCore.Qt.UserRole)
            data = {
                "token": self.token,
                "current_op_id": self.op_id,
                "import_op_id": import_op_id
            }
            url = url_join(self.mscolab_server_url, 'import_permissions')
            res = requests.post(url, data=data)
            if res.text != "False":
                res = res.json()
                if res["success"]:
                    self.load_users_without_permission()
                    self.load_users_with_permission()
                else:
                    show_popup(self, "Error", res["message"])
            else:
                # this triggers disconnect
                self.conn.signal_reload.emit(self.op_id)
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    # Socket Events
    def handle_permissions_updated(self, u_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            if self.user["id"] == u_id:
                return

            show_popup(self, 'Alert',
                       'The permissions for this operation were updated! The window is going to refresh.', 1)
            self.load_import_operations()
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            # this triggers disconnect
            self.conn.signal_reload.emit(self.op_id)

    def closeEvent(self, event):
        self.viewCloses.emit()
        event.accept()
