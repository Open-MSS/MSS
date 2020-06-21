# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab_change_history
    ~~~~~~~~~~~~~~~~~~~~~

    Mscolab change history window to display the change history of the flight path so that users
    can revert back to a previous version

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
from mslib.msui.mss_qt import ui_mscolab_change_history as ui
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader

import logging
import requests
import json


class MSColabChangeHistory(QtWidgets.QMainWindow, ui.Ui_ChangeHistory):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Change History Window"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, token, p_id, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB", default=mss_default.default_MSCOLAB)):
        """
        token: access_token
        p_id: project id
        """
        super(MSColabChangeHistory, self).__init__(parent)
        self.setupUi(self)

        # set url
        self.mscolab_server_url = mscolab_server_url

        self.token = token
        self.p_id = p_id
        self.conn = conn
        logging.debug(ui.Ui_ChangeHistory)
        # establish button press handlers

        self.checkout.clicked.connect(self.handle_undo)

        # load changes
        self.load_all_changes()
        # active change
        self.active_ch_id = None
        user_d = self.get_user_details(self.token)
        proj_d = self.get_project_details(self.p_id)
        self.user_info.setText("logged in as: {}".format(user_d["username"]))
        self.proj_info.setText("Project name: {}".format(proj_d["path"]))

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

    def handle_undo(self):
        index = self.changes.currentIndex()
        qm = QtWidgets.QMessageBox
        if not index.isValid():
            qm.critical(
                self, self.tr("Undo"),
                self.tr("Please select a change first."))
        else:
            ret = qm.question(
                self, self.tr("Undo"),
                "Do you want to checkout to this change?", qm.Yes, qm.No)

            if ret == qm.Yes:
                self.request_undo_mscolab(index)

    def request_undo_mscolab(self, index):
        # undo change from server
        data = {
            "token": self.token,
            "ch_id": self.changes.itemFromIndex(index)._id
        }
        # 'undo' request
        r = requests.post(self.mscolab_server_url + '/undo', data=data)
        if r.text == "True":
            # reload windows
            self.reloadWindows.emit()

    def closeEvent(self, event):
        self.viewCloses.emit()
