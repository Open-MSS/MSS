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
import json
import requests
from werkzeug.urls import url_join

from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui.mss_qt import QtCore, QtWidgets
from mslib.msui.mss_qt import ui_mscolab_version_history as ui
from mslib.utils import config_loader


class MSColabVersionHistory(QtWidgets.QMainWindow, ui.Ui_MscolabVersionHistory):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Version History Window"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    reloadWindows = QtCore.pyqtSignal(name="reloadWindows")

    def __init__(self, token, p_id, user, project_name, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB", default=mss_default.default_MSCOLAB)):
        """
        token: access_token
        p_id: project id
        user: logged in user
        project_name: name of project,
        conn: socket connection
        parent: parent of widget
        mscolab_server_url: server url of mscolab
        """
        super(MSColabVersionHistory, self).__init__(parent)
        self.setupUi(self)

        self.token = token
        self.p_id = p_id
        self.user = user
        self.project_name = project_name
        self.conn = conn
        self.mscolab_server_url = mscolab_server_url
        # Event handlers
        self.checkout.clicked.connect(self.handle_undo)
        # active change
        self.active_ch_id = None
        self.set_label_text()
        self.load_all_changes()

    def set_label_text(self):
        self.usernameLabel.setText(f"Logged in: {self.user['username']}")
        self.projectNameLabel.setText(f"Project: {self.project_name}")

    def load_all_changes(self):
        """
        get changes from api, clear listwidget, render them to ui
        """
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        # 'get all changes' request
        url = url_join(self.mscolab_server_url, 'get_changes')
        r = requests.get(url, data=data)
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
        url = url_join(self.mscolab_server_url, 'undo')
        r = requests.post(url, data=data)
        if r.text == "True":
            # reload windows
            self.reloadWindows.emit()

    def closeEvent(self, event):
        self.viewCloses.emit()
