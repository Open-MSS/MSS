# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_operation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-operation related gui.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import os
import sys
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message
from PyQt5 import QtCore, QtTest, QtWidgets
from tests.utils import mscolab_start_server
from mslib.msui import mscolab
from mslib.msui import msui
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation

PORTS = list(range(22000, 22500))


class Actions(object):
    DOWNLOAD = 0
    COPY = 1
    REPLY = 2
    EDIT = 3
    DELETE = 4


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_MscolabOperation(object):
    def setup_method(self):
        handle_db_reset()
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.show()
        # connect and login to mscolab
        self._connect_to_mscolab()
        self._login(self.userdata[0], self.userdata[2])
        # activate operation and open chat window
        self._activate_operation_at_index(0)
        self.window.actionChat.trigger()
        QtWidgets.QApplication.processEvents()
        self.chat_window = self.window.mscolab.chat_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown_method(self):
        self.window.mscolab.logout()
        if self.window.mscolab.chat_window:
            self.window.mscolab.chat_window.hide()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_send_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        with self.app.app_context():
            assert Message.query.filter_by(text='**test message**').count() == 2

    def test_search_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        message_index = self.chat_window.messageList.count() - 1
        # self.window.chat_window.searchMessageLineEdit.setText("test message")
        self.chat_window.searchMessageLineEdit.setText("test message")
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index).isSelected() is True
        QtTest.QTest.mouseClick(self.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index - 1).isSelected() is True
        QtTest.QTest.mouseClick(self.chat_window.searchNextBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.chat_window.messageList.item(message_index).isSelected() is True

    def test_copy_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        self._activate_context_menu_action(Actions.COPY)
        assert QtWidgets.QApplication.clipboard().text() == "**test message**"

    def test_reply_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        parent_message_id = self._get_message_id(self.chat_window.messageList.count() - 1)
        self._activate_context_menu_action(Actions.REPLY)
        self.chat_window.messageText.setPlainText('test reply')
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(100)
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
        QtTest.QTest.qWait(100)
        with self.app.app_context():
            assert Message.query.filter_by(text='test edit').count() == 1

    def test_delete_message(self):
        self._send_message("**test message**")
        self._send_message("**test message**")
        self._activate_context_menu_action(Actions.DELETE)
        QtTest.QTest.qWait(100)
        with self.app.app_context():
            assert Message.query.filter_by(text='test edit').count() == 0

    def _connect_to_mscolab(self):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self, emailid, password):
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _activate_operation_at_index(self, index):
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _activate_context_menu_action(self, action_index):
        item = self.chat_window.messageList.item(self.chat_window.messageList.count() - 1)
        message_widget = self.chat_window.messageList.itemWidget(item)
        message_widget.context_menu.actions()[action_index].trigger()

    def _send_message(self, text):
        self.chat_window.messageText.setPlainText(text)
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _get_message_id(self, index):
        item = self.chat_window.messageList.item(index)
        message_widget = self.chat_window.messageList.itemWidget(item)
        return message_widget.id
