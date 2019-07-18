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

from mslib.msui.mss_qt import QtCore, QtWidgets
from mslib.msui.mss_qt import ui_mscolab_project_window as ui
import logging


class MSColabProjectWindow(QtWidgets.QWidget, ui.Ui_MscolabProject):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "MSColab Project Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, token, p_id, conn):
        """
        token: access_token
        p_id: project id
        conn: to send messages, recv messages, if a direct slot-signal can't be setup
            to be connected at parents'
        """
        self.token = token
        self.p_id = p_id
        self.conn = conn

        # establish button press handlers
        self.add.clicked.connect(self.add_handler)
        self.modify.clicked.connect(self.modify_handler)
        self.delete_1.clicked.connect(self.delete_handler)

    def add_handler(self):
        # get username, p_id
        username = self.username.text()
        p_id = self.p_id
        # send request to add
        pass

    def modify_handler(self):
        # get username, p_id
        username = self.username.text()
        p_id = self.p_id
        # send request to modify
        pass

    def delete_handler(self):
        # get username, p_id
        username = self.username.text()
        p_id = self.p_id
        # send request to delete
        pass
