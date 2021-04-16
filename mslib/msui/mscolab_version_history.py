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
from datetime import datetime
import json

import requests
from werkzeug.urls import url_encode, url_join

from mslib.msui.flighttrack import WaypointsTableModel
from PyQt5 import QtCore, QtWidgets, QtGui
from mslib.msui.qt5 import ui_mscolab_version_history as ui
from mslib.utils import config_loader, show_popup, utc_to_local_datetime


class MSColabVersionHistory(QtWidgets.QMainWindow, ui.Ui_MscolabVersionHistory):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Version History Window"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")
    reloadWindows = QtCore.pyqtSignal(name="reloadWindows")

    def __init__(self, token, p_id, user, project_name, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB")):
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
        # Initialise Variables
        self.token = token
        self.p_id = p_id
        self.user = user
        self.project_name = project_name
        self.conn = conn
        self.mscolab_server_url = mscolab_server_url

        # Event handlers
        self.refreshBtn.clicked.connect(self.handle_refresh)
        self.checkoutBtn.clicked.connect(self.handle_undo)
        self.nameVersionBtn.clicked.connect(self.handle_named_version)
        self.deleteVersionNameBtn.clicked.connect(self.handle_delete_version_name)
        self.versionFilterCB.currentIndexChanged.connect(lambda: self.load_all_changes())
        self.changes.currentItemChanged.connect(self.preview_change)
        # Setup UI
        self.deleteVersionNameBtn.setVisible(False)
        self.set_label_text()
        self.set_change_list_style()
        self.toggle_version_buttons(False)
        self.load_current_waypoints()
        self.load_all_changes()

    def set_label_text(self):
        self.usernameLabel.setText(f"Logged in: {self.user['username']}")
        self.projectNameLabel.setText(f"Project: {self.project_name}")

    def set_change_list_style(self):
        palette = self.changes.palette()
        self.changes.setStyleSheet(f"""
            QListWidget::item {{
                border-bottom: 1px solid #222;
            }}
            QListWidget::item:selected {{
                background-color: {palette.highlight().color().name()};
                color: {palette.highlightedText().color().name()};
            }}
        """)

    def toggle_version_buttons(self, state):
        self.checkoutBtn.setEnabled(state)
        self.nameVersionBtn.setEnabled(state)

    def load_current_waypoints(self):
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        url = url_join(self.mscolab_server_url, 'get_project_by_id')
        res = requests.get(url, data=data)
        xml_content = json.loads(res.text)["content"]
        waypoint_model = WaypointsTableModel(name="Current Waypoints", xml_content=xml_content)
        self.currentWaypointsTable.setModel(waypoint_model)

    def load_all_changes(self):
        """
        get changes from api, clear listwidget, render them to ui
        """
        data = {
            "token": self.token,
            "p_id": self.p_id
        }
        named_version_only = None
        if self.versionFilterCB.currentIndex() == 0:
            named_version_only = True
        query_string = url_encode({"named_version": named_version_only})
        url_path = f'get_all_changes?{query_string}'
        url = url_join(self.mscolab_server_url, url_path)
        r = requests.get(url, data=data)
        changes = json.loads(r.text)["changes"]
        self.changes.clear()
        for change in changes:
            created_at = datetime.strptime(change["created_at"], "%Y-%m-%d, %H:%M:%S")
            local_time = utc_to_local_datetime(created_at)
            date = local_time.strftime('%d/%m/%Y')
            time = local_time.strftime('%I:%M %p')
            item_text = f'{change["username"]} made change on {date} at {time}'
            if change["version_name"] is not None:
                item_text = f'{change["version_name"]}\n{item_text}'
            item = QtWidgets.QListWidgetItem(item_text, parent=self.changes)
            item.id = change["id"]
            item.version_name = change["version_name"]
            self.changes.addItem(item)

    def preview_change(self, current_item, previous_item):
        font = QtGui.QFont()
        if previous_item is not None:
            previous_item.setFont(font)

        if current_item is None:
            self.changePreviewTable.setModel(None)
            self.deleteVersionNameBtn.setVisible(False)
            self.toggle_version_buttons(False)
            return

        font.setBold(True)
        current_item.setFont(font)
        data = {
            "token": self.token,
            "ch_id": current_item.id
        }
        url = url_join(self.mscolab_server_url, 'get_change_content')
        res = requests.get(url, data=data).json()
        waypoint_model = WaypointsTableModel(xml_content=res["content"])
        self.changePreviewTable.setModel(waypoint_model)
        if current_item.version_name is not None:
            self.deleteVersionNameBtn.setVisible(True)
        else:
            self.deleteVersionNameBtn.setVisible(False)
        self.toggle_version_buttons(True)

    def request_set_version_name(self, version_name, ch_id):
        data = {
            "token": self.token,
            "version_name": version_name,
            "ch_id": ch_id,
            "p_id": self.p_id
        }
        url = url_join(self.mscolab_server_url, 'set_version_name')
        res = requests.post(url, data=data)
        return res

    def handle_named_version(self):
        version_name, completed = QtWidgets.QInputDialog.getText(self, 'Version Name Dialog', 'Enter version name:')
        if completed is True:
            if len(version_name) > 255 or len(version_name) == 0:
                show_popup(self, "Error", "Version name length has to be between 1 and 255")
                return
            selected_item = self.changes.currentItem()
            res = self.request_set_version_name(version_name, selected_item.id)
            res = res.json()
            if res["success"] is True:
                item_text = selected_item.text().split('\n')[-1]
                new_text = f"{version_name}\n{item_text}"
                selected_item.setText(new_text)
                selected_item.version_name = version_name
                self.deleteVersionNameBtn.setVisible(True)
            else:
                show_popup(self, "Error", res["message"])

    def handle_delete_version_name(self):
        selected_item = self.changes.currentItem()
        res = self.request_set_version_name(None, selected_item.id)
        res = res.json()
        if res["success"] is True:
            # Remove item if the filter is set to Named version
            if self.versionFilterCB.currentIndex() == 0:
                self.changes.takeItem(self.changes.currentRow())
            # Remove name from item
            else:
                item_text = selected_item.text().split('\n')[-1]
                selected_item.setText(item_text)
                selected_item.version_name = None
            self.deleteVersionNameBtn.setVisible(False)
        else:
            show_popup(self, "Error", res["message"])

    def handle_undo(self):
        qm = QtWidgets.QMessageBox
        ret = qm.question(self, self.tr("Undo"), "Do you want to checkout to this change?", qm.Yes, qm.No)
        if ret == qm.Yes:
            data = {
                "token": self.token,
                "ch_id": self.changes.currentItem().id
            }
            url = url_join(self.mscolab_server_url, 'undo')
            r = requests.post(url, data=data)
            if r.text == "True":
                # reload windows
                self.reloadWindows.emit()
                self.load_current_waypoints()
                self.load_all_changes()

    def handle_refresh(self):
        self.load_current_waypoints()
        self.load_all_changes()

    def closeEvent(self, event):
        self.viewCloses.emit()
