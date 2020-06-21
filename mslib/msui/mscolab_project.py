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
from PyQt5.QtWidgets import QWidget

from mslib.msui.mss_qt import QtCore, QtWidgets, QtGui
from mslib.msui.mss_qt import ui_mscolab_project_window as ui
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader

from markdown import Markdown
from markdown.extensions import Extension
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

    def __init__(self, token, p_id, user, project_name, access_level, conn, parent=None,
                 mscolab_server_url=config_loader(dataset="default_MSCOLAB", default=mss_default.default_MSCOLAB)):
        """
        token: access_token
        p_id: project id
        user: logged in user
        project_name: active project name,
        access_level: access level of user logged in
        conn: to send messages, recv messages, if a direct slot-signal can't be setup
            to be connected at parents'
        parent: widget parent
        mscolab_server_url: server url for mscolab
        """
        super(MSColabProjectWindow, self).__init__(parent)
        self.setupUi(self)

        self.mscolab_server_url = mscolab_server_url
        self.token = token
        self.user = user
        self.p_id = p_id
        self.project_name = project_name
        self.conn = conn
        self.access_level = access_level
        self.text = ""
        self.messages = []
        self.markdown = Markdown(extensions=['nl2br', 'sane_lists', DeregisterSyntax()])

        # Signals
        self.sendMessage.clicked.connect(self.send_message)
        self.previewBtn.clicked.connect(self.toggle_preview)

        # Socket Connection handlers
        self.conn.signal_message_receive.connect(self.render_new_message)

        # Set Label text
        self.set_label_text()

        # load all users
        self.load_users()

        # load messages
        self.load_all_messages()

    # UI SET UP METHODS
    def set_label_text(self):
        self.user_info.setText(f"Logged in: {self.user['username']}")
        self.proj_info.setText(f"Project: {self.project_name}")

    # Signal Slots

    def send_message(self):
        """
        send message through connection
        """
        message_text = self.messageText.toPlainText()
        self.conn.send_message(message_text, self.p_id)
        self.messageText.clear()

    def toggle_preview(self):
        # Go Back to text box
        if self.messageText.isReadOnly():
            self.messageText.setHtml("")
            self.messageText.setText(self.text)
            self.messageText.moveCursor(QtGui.QTextCursor.End)
            self.messageText.setReadOnly(False)
            self.previewBtn.setDefault(False)
        # Show preview
        else:
            self.text = self.messageText.toPlainText()
            html = self.markdown.convert(self.text)
            self.messageText.setHtml(html)
            self.messageText.setReadOnly(True)
            self.previewBtn.setDefault(True)

    # API REQUESTS

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
        # clear message box
        for message in messages:
            username = message["username"]
            message_text = message["text"]
            self.render_new_message(username, message_text, False)
        self.messageList.scrollToBottom()

    # SOCKET HANDLERS

    @QtCore.Slot(str, str)
    def render_new_message(self, username, message, scroll=True):
        message_item = MessageItem(username, message, self.user["username"], self.markdown)
        list_widget_item = QtWidgets.QListWidgetItem(self.messageList)
        list_widget_item.setSizeHint(message_item.sizeHint())
        self.messageList.addItem(list_widget_item)
        self.messageList.setItemWidget(list_widget_item, message_item)
        self.messages.append(message_item)
        if scroll:
            self.messageList.scrollToBottom()

    def closeEvent(self, event):
        self.viewCloses.emit()


class MessageItem(QtWidgets.QWidget):
    def __init__(self, username, message_text, current_username, markdown_helper):
        super(MessageItem, self).__init__()
        self.username = username
        self.message_text = message_text
        self.current_username = current_username
        self.messageTextEdit = QtWidgets.QTextEdit()
        html = markdown_helper.convert(self.message_text)
        self.messageTextEdit.setHtml(html)
        self.messageTextEdit.setReadOnly(True)
        self.messageTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.messageTextEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.messageTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.messageTextEdit.setAttribute(103)
        self.messageTextEdit.show()
        self.messageTextEdit.setFixedHeight(
            self.messageTextEdit.document().size().height() + self.messageTextEdit.contentsMargins().top() * 2
        )
        self.containerLayout = QtWidgets.QHBoxLayout()

        if current_username == username:
            self.messageTextEdit.setStyleSheet("background: #dcf8c6")
            self.containerLayout.addStretch()
            self.containerLayout.addWidget(self.messageTextEdit)

        else:
            self.messageTextEdit.setStyleSheet("background: transparent; border: none;")
            self.textArea = QtWidgets.QWidget()
            self.textAreaLayout = QtWidgets.QVBoxLayout()
            self.usernameLabel = QtWidgets.QLabel(f"{self.username}:")
            self.textAreaLayout.addWidget(self.usernameLabel)
            self.textAreaLayout.addWidget(self.messageTextEdit)
            self.textArea.setLayout(self.textAreaLayout)
            self.textArea.setStyleSheet("background: #eff0f1")
            self.containerLayout.addWidget(self.textArea)
            self.containerLayout.addStretch()

        self.containerLayout.setSpacing(0)
        self.containerLayout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.containerLayout)

# Deregister all the syntax that we don't want to allow
# Can't find any part in documentation where all the syntax names are mentioned
# For future reference to syntax name refer to:
# https://github.com/Python-Markdown/markdown/blob/a06659b62209de98cbc23715addb2b768a245788/markdown/core.py#L100
class DeregisterSyntax(Extension):
    def extendMarkdown(self, md):
        # Deregister block syntax
        md.parser.blockprocessors.deregister('hashheader')
        md.parser.blockprocessors.deregister('setextheader')
        md.parser.blockprocessors.deregister('hr')
        md.parser.blockprocessors.deregister('quote')

        # Deregister inline syntax
        md.inlinePatterns.deregister('reference')
        md.inlinePatterns.deregister('link')
        md.inlinePatterns.deregister('image_link')
        md.inlinePatterns.deregister('image_reference')
        md.inlinePatterns.deregister('short_reference')
        md.inlinePatterns.deregister('autolink')
        md.inlinePatterns.deregister('automail')
        md.inlinePatterns.deregister('linebreak')
        md.inlinePatterns.deregister('html')
        md.inlinePatterns.deregister('entity')