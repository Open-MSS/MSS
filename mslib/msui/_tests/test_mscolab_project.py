# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
import sys
import time

from mslib.msui.mscolab import MSSMscolabWindow
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message
from PyQt5 import QtCore, QtTest, QtWidgets, Qt
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9571, 9590))


class Actions(object):
    DOWNLOAD = 0
    COPY = 1
    REPLY = 2
    EDIT = 3
    DELETE = 4


class Test_MscolabProject(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.5)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.window.show()
        self._login()
        self._activate_project_at_index(0)
        # activate project window here by clicking button
        QtTest.QTest.mouseClick(self.window.chatWindowBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.chat_window = self.window.chat_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        # to disconnect connections, and clear token
        # Not logging out since it pops up a dialog
        # self.window.logout()
        if self.window.chat_window:
            self.window.chat_window.hide()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_send_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        # wait till server processes the change
        with self.app.app_context():
            assert Message.query.filter_by(text='**test message**').count() == 2

    def test_search_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        # wait till server processes the change
        message_index = self.window.chat_window.messageList.count()
        self.window.chat_window.searchMessageLineEdit.setText("test message")
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index).isSelected() is True
        QtTest.QTest.mouseClick(self.window.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index - 1).isSelected() is True
        QtTest.QTest.mouseClick(self.window.chat_window.searchNextBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index).isSelected() is True

    def test_copy_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        # wait till server processes the change
        time.sleep(0.5)
        self._activate_context_menu_action(Actions.COPY)
        assert Qt.QApplication.clipboard().text() == "**test message**"

    def test_reply_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        # wait till server processes the change
        time.sleep(0.5)
        parent_message_id = self._get_message_id(self.chat_window.messageList.count() - 1)
        self._activate_context_menu_action(Actions.REPLY)
        self.chat_window.messageText.setPlainText('test reply')
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)
        time.sleep(0.5)
        with self.app.app_context():
            message = Message.query.filter_by(text='test reply')
            assert message.count() == 1
            assert message.first().reply_id == parent_message_id

    def test_edit_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        self._activate_context_menu_action(Actions.EDIT)
        self.chat_window.messageText.setPlainText('test edit')
        QtTest.QTest.mouseClick(self.chat_window.editMessageBtn, QtCore.Qt.LeftButton)
        time.sleep(0.5)
        with self.app.app_context():
            assert Message.query.filter_by(text='test edit').count() == 1

    def test_delete_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        self._activate_context_menu_action(Actions.DELETE)
        time.sleep(0.5)
        with self.app.app_context():
            assert Message.query.filter_by(text='test edit').count() == 0

    def _connect_to_mscolab(self):
        self.window.url.setEditText(self.url)
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self):
        # login
        self._connect_to_mscolab()
        self.window.emailid.setText('a')
        self.window.password.setText('a')
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _activate_context_menu_action(self, action_index):
        item = self.chat_window.messageList.item(self.chat_window.messageList.count() - 1)
        message_widget = self.chat_window.messageList.itemWidget(item)
        message_widget.context_menu.actions()[action_index].trigger()

    def _send_message(self, text):
        self.chat_window.messageText.setPlainText(text)
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(0.5)

    def _get_message_id(self, index):
        item = self.chat_window.messageList.item(index)
        message_widget = self.chat_window.messageList.itemWidget(item)
        return message_widget.id
