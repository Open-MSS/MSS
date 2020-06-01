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

from mslib.msui.mss_qt import QtCore, QtWidgets
from mslib.msui.mss_qt import ui_mscolab_admin_window as ui
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader
import requests
import json


class MSColabAdminWindow(QtWidgets.QMainWindow, ui.Ui_MscolabAdminWindow):

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, token, p_id, user, project_name, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB", default=mss_default.default_MSCOLAB)):
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
        self.conn = conn

        self.addUsers = []
        self.modifyUsers = []

        # Button click handlers
        self.addUsersBtn.clicked.connect(self.add_selected_users)
        self.modifyUsersBtn.clicked.connect(self.modify_selected_users)
        self.deleteUsersBtn.clicked.connect(self.delete_selected_users)
        self.selectAllAddBtn.clicked.connect(lambda: self.select_all(self.addUsersTable))
        self.deselectAllAddBtn.clicked.connect(lambda: self.deselect_all(self.addUsersTable))
        self.selectAllModifyBtn.clicked.connect(lambda: self.select_all(self.modifyUsersTable))
        self.deselectAllModifyBtn.clicked.connect(lambda: self.deselect_all(self.modifyUsersTable))

        self.set_label_text()
        self.load_users_without_permission()
        self.load_users_with_permission()

    def populate_table(self, table, users):
        table.setRowCount(0)
        for row_number, row_data in enumerate(users):
            table.insertRow(row_number)
            for col_number, item in enumerate(row_data):
                new_item = QtWidgets.QTableWidgetItem(item)
                table.setItem(row_number, col_number, new_item)

    def get_selected_userids(self, table, users):
        u_ids = []
        selected_rows = table.selectionModel().selectedRows()
        for row in selected_rows:
            u_ids.append(users[row.row()][-1])

        return u_ids

    def select_all(self, table):
        table.setFocus()
        for row_num in range(table.rowCount()):
            if table.item(row_num, 0).isSelected() is False:
                table.selectRow(row_num)

    def deselect_all(self, table):
        table.setFocus()
        for row_num in range(table.rowCount()):
            if table.item(row_num, 0).isSelected():
                table.selectRow(row_num)

    def set_label_text(self):
        self.projectNameLabel.setText(f"Project: {self.project_name}")
        self.usernameLabel.setText(f"Logged In: {self.user['username']}")

    def load_users_without_permission(self):
        self.addUsers = []
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        res = requests.get(self.mscolab_server_url + "/users_without_permission", data=data)
        res = res.json()
        self.addUsers = res["users"]
        self.populate_table(self.addUsersTable, self.addUsers)

    def load_users_with_permission(self):
        self.modifyUsers = []
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        res = requests.get(self.mscolab_server_url + "/users_with_permission", data=data)
        res = res.json()
        self.modifyUsers = res["users"]
        self.populate_table(self.modifyUsersTable, self.modifyUsers)

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
        res = requests.post(self.mscolab_server_url + "/add_bulk_permissions", data=data)
        res = res.json()
        if res["success"]:
            # TODO: Do we need a success popup?
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            self.show_error_popup(res["message"])

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
        res = requests.post(self.mscolab_server_url + "/modify_bulk_permissions", data=data)
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
        res = requests.post(self.mscolab_server_url + "/delete_bulk_permissions", data=data)
        res = res.json()
        print("res:", res)
        if res["success"]:
            self.load_users_without_permission()
            self.load_users_with_permission()
        else:
            self.show_error_popup(res["message"])

    def show_error_popup(self, message):
        error_msg = QtWidgets.QMessageBox()
        error_msg.setWindowTitle("Error")
        error_msg.setText(message)
        error_msg.setIcon(QtWidgets.QMessageBox.Critical)
        error_msg.exec_()

    def closeEvent(self, event):
        self.viewCloses.emit()

    # TODO: DO WE NEED SOCKET EVENT UPDATES FOR ADMIN WINDOW?
