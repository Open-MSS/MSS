# -*- coding: utf-8 -*-
"""

    mslib.msui.mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Window to display authentication and project details for mscolab


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of mss.

    :copyright: Copyright 2019- Shivashis Padhi
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

from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore
from mslib.msui.mss_qt import ui_mscolab_window as ui
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui.icons import icons

import logging
import requests
import json


class MSSMscolabWindow(QtWidgets.QMainWindow, ui.Ui_MSSMscolabWindow):
    """PyQt window implementing mscolab window
    """
    name = "Mscolab"
    identifier = None
    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None):
        """Set up user interface
        """
        super(MSSMscolabWindow, self).__init__(parent)
        self.setupUi(self)
        self.widget_2.hide()
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))
        # if token is None, not authorized, else authorized
        self.token = None
        self.loginButton.clicked.connect(self.authorize)
        self.logoutButton.clicked.connect(self.logout)
        self.topview.clicked.connect(self.open_topview)
        self.sideview.clicked.connect(self.open_sideview)
        self.tableview.clicked.connect(self.open_tableview)

        # bool to store active pid
        self.active_pid = None

    def authorize(self):
        emailid = self.emailid.text()
        password = self.password.text()
        data = {
            "email": emailid,
            "password": password
        }
        r = requests.post(mss_default.mscolab_server_url + '/token', data=data)
        if r.text == "False":
            # popup that wrong credentials
            self.error_dialog = QtWidgets.QErrorMessage()
            self.error_dialog.showMessage('Oh no, your credentials were incorrect.')
            pass
        else:
            # remove the login modal and put text there
            json_ = json.loads(r.text)
            logging.debug(json_["token"])
            self.token = json_["token"]
            self.label.setText("logged in as: " + json_["user"]["username"])
            self.widget_2.show()
            self.widget.hide()

            # add projects
            data = {
                "token": self.token
            }
            r = requests.get(mss_default.mscolab_server_url + '/projects', data=data)
            json_ = json.loads(r.text)
            projects = json_["projects"]
            self.add_projects_to_ui(projects)

    def add_projects_to_ui(self, projects):
        for project in projects:
            project_desc = project['path'] + " (" + project["access_level"] + ")"
            widgetItem = QtWidgets.QListWidgetItem(project_desc, parent=self.listProjects)
            widgetItem.p_id = project["p_id"]
            self.listProjects.addItem(widgetItem)
        self.listProjects.itemActivated.connect(self.set_active_pid)

    def set_active_pid(self, item):
        self.active_pid = item.p_id
        logging.debug(self.active_pid)
        font = QtGui.QFont()
        for i in range(self.listProjects.count()):
            self.listProjects.item(i).setFont(font)
        font.setBold(True)
        item.setFont(font)

    def open_topview(self):
        # showing dummy info dialog
        if self.active_pid == None:
            return
        self.i_dialog = QtWidgets.QErrorMessage()
        self.i_dialog.showMessage('Opening topview with p_id'+str(self.active_pid))

    def open_sideview(self):
        # showing dummy info dialog
        if self.active_pid == None:
            return
        self.i_dialog = QtWidgets.QErrorMessage()
        self.i_dialog.showMessage('Opening sideview with p_id'+str(self.active_pid))

    def open_tableview(self):
        # showing dummy info dialog
        if self.active_pid == None:
            return
        self.i_dialog = QtWidgets.QErrorMessage()
        self.i_dialog.showMessage('Opening tableview with p_id'+str(self.active_pid))

    def logout(self):
        # delete token and show login widget-items
        self.token = None
        # clear projects list here
        self.widget_2.hide()
        self.widget.show()

    def setIdentifier(self, identifier):
        self.identifier = identifier
