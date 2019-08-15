# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~

    Mscolab project window, to display chat, file change

    This file is part of mss.

    :copyright: 2019 Shivashis Padhi
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

from mslib.msui.mss_qt import QtCore, QtWidgets, QtGui
from mslib.msui.mss_qt import ui_mscolab_project_window as ui
from mslib._tests.constants import MSCOLAB_URL

import logging
import requests
import json
import datetime


class MSColabProjectWindow(QtWidgets.QMainWindow, ui.Ui_MscolabProject):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Project Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    reloadWindows = QtCore.pyqtSignal(name="reloadWindows")

    def __init__(self, token, p_id, conn, access_level, parent=None, mscolab_server_url=MSCOLAB_URL):
        """
        token: access_token
        p_id: project id
        conn: to send messages, recv messages, if a direct slot-signal can't be setup
            to be connected at parents'
        """
        super(MSColabProjectWindow, self).__init__(parent)
        self.setupUi(self)
        # set url
        self.mscolab_server_url = mscolab_server_url

        # constrain vertical layout
        # self.verticalLayout.setSizeConstraint(self.verticalLayout_6.SetMinimumSize)
        # self.messages.setWordWrap(True)

        self.token = token
        self.p_id = p_id
        self.conn = conn
        self.access_level = access_level
        # add receive message handler
        self.conn.signal_message_receive.connect(self.render_new_message)
        logging.debug(ui.Ui_MscolabProject)
        # establish button press handlers
        self.add.clicked.connect(self.add_handler)
        self.modify.clicked.connect(self.modify_handler)
        self.delete_1.clicked.connect(self.delete_handler)
        self.checkout.clicked.connect(self.handle_undo)
        # send message handler
        self.sendMessage.clicked.connect(self.send_message)
        # load users
        self.load_users()
        # load changes
        self.load_all_changes()
        # load messages
        self.load_all_messages()
        # active change
        self.active_ch_id = None
        user_d = self.get_user_details(self.token)
        proj_d = self.get_project_details(self.p_id)
        self.user_info.setText("logged in as: {}".format(user_d["username"]))
        self.proj_info.setText("Project name: {}".format(proj_d["path"]))
        # disable admin actions if viewer or collaborator
        if self.access_level == "collaborator" or self.access_level == "viewer":
            self.add.setEnabled(False)
            self.modify.setEnabled(False)
            self.delete_1.setEnabled(False)
        if self.access_level == "viewer":
            self.checkout.setEnabled(False)
            self.sendMessage.setEnabled(False)

    def get_user_details(self, token):
        """
        token: auth token of the user to be fetched from mscolab server
        """
        data = {
            'token': token
        }
        r = requests.get(self.mscolab_server_url + '/user', data=data)
        json_ = json.loads(r.text)
        return json_['user']

    def get_project_details(self, p_id):
        """
        p_id: active project id details of which are fetched from mscolab server
        """
        data = {
            'token': self.token,
            'p_id': p_id
        }
        r = requests.get(self.mscolab_server_url + '/project_details', data=data)
        json_ = json.loads(r.text)
        return json_

    def send_message(self):
        """
        send message through connection
        """
        message_text = self.messageText.toPlainText()
        self.conn.send_message(message_text, self.p_id)
        self.messageText.clear()

    def add_handler(self):
        # get username, p_id
        username = self.username.text()
        access_level = str(self.accessLevel.currentText())
        # send request to add
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "username": username,
            "access_level": access_level
        }
        r = requests.post(self.mscolab_server_url + '/add_permission', data=data)
        if r.text == "True":
            self.load_users()
        else:
            # show a QMessageBox with errors
            pass

    def modify_handler(self):
        # get username, p_id
        username = self.username.text()
        access_level = str(self.accessLevel.currentText())
        # send request to modify
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "username": username,
            "access_level": access_level
        }
        r = requests.post(self.mscolab_server_url + '/modify_permission', data=data)
        if r.text == "True":
            self.load_users()
        else:
            # show a QMessageBox with errors
            pass

    def delete_handler(self):
        # get username, p_id
        username = self.username.text()
        p_id = self.p_id
        # send request to delete
        data = {
            "token": self.token,
            "p_id": p_id,
            "username": username
        }
        r = requests.post(self.mscolab_server_url + '/revoke_permission', data=data)
        if r.text == "True":
            self.load_users()
        else:
            # show a QMessageBox with errors
            pass

    def load_users(self):
        # load users to side-tab here

        # make request to get users
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        r = requests.get(self.mscolab_server_url + '/authorized_users', data=data)
        if r.text == "False":
            # show QMessageBox errors here
            pass
        else:
            self.collaboratorsList.clear()
            users = json.loads(r.text)["users"]
            for user in users:
                item = QtWidgets.QListWidgetItem("{} - {}".format(user["username"],
                                                 user["access_level"]),
                                                 parent=self.collaboratorsList)
                item.username = user["username"]
                self.collaboratorsList.addItem(item)
            self.collaboratorsList.itemActivated.connect(self.update_username_wrt_item)

    def update_username_wrt_item(self, item):
        self.username.setText(item.username)

    @QtCore.Slot(str, str)
    def render_new_message(self, username, message, scroll=True):
        item = QtWidgets.QListWidgetItem("{}: {}\n".format(username, message), parent=self.messages)
        self.messages.addItem(item)
        if scroll:
            self.messages.scrollToBottom()

    def load_all_changes(self):
        """
        get changes from api, clear listwidget, render them to ui
        """
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        # 'get all changes' request
        r = requests.get(self.mscolab_server_url + '/get_changes', data=data)
        changes = json.loads(r.text)["changes"]
        self.changes.clear()
        self.active_ch_id = None
        for change in changes:
            item = QtWidgets.QListWidgetItem("{}: {}\n".format(change["username"],
                                             change["content"]), parent=self.changes)
            item._id = change['id']
            self.changes.addItem(item)
        self.changes.scrollToBottom()
        self.changes.itemActivated.connect(self.handle_change_activate)

    def handle_change_activate(self, item):
        self.active_ch_id = item._id
        # change font style for selected
        font = QtGui.QFont()
        for i in range(self.changes.count()):
            self.changes.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def handle_undo(self):
        if self.active_ch_id is None:
            return

        self.qm = QtWidgets.QMessageBox
        self.w = QtWidgets.QWidget()
        ret = self.qm.question(self.w, 'Undo', "Do you want to checkout to this change?", self.qm.Yes, self.qm.No)
        if ret == self.qm.Yes:
            self.request_undo_mscolab()
        return

    def request_undo_mscolab(self):
        # undo change from server
        data = {
            "token": self.token,
            "ch_id": self.active_ch_id
        }
        # 'undo' request
        r = requests.post(self.mscolab_server_url + '/undo', data=data)
        if r.text == "True":
            # reload windows
            self.reloadWindows.emit()

    def load_all_messages(self):
        # empty messages and reload from server
        data = {
            "token": self.token,
            "p_id": self.p_id,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%m %d %Y, %H:%M:%S")
        }
        # returns an array of messages
        r = requests.post(self.mscolab_server_url + "/messages", data=data)
        response = json.loads(r.text)

        messages = response["messages"]
        logging.debug(messages)
        logging.debug(type(messages))
        # clear message box
        self.messages.clear()
        for message in messages:
            username = message["username"]
            message_text = message["text"]
            self.render_new_message(username, message_text, scroll=False)
        self.messages.scrollToBottom()

    def closeEvent(self, event):
        self.viewCloses.emit()
