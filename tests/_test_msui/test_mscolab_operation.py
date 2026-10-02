# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_operation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-operation related gui.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
import pytest
import datetime
import json

import mock
import requests

from tests.constants import ROOT_DIR
from mslib.msui.icons import icons
from mslib.mscolab.models import Message, MessageType
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.msui import mscolab
from mslib.msui import msui
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation
from mslib.utils.config import modify_config_file
from mslib.mscolab.utils import get_message_dict


class Actions:
    DOWNLOAD = 0
    COPY = 1
    REPLY = 2
    EDIT = 3
    DELETE = 4


class Test_MscolabOperation:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mscolab_server_app, mscolab_server):
        self.app = mscolab_server_app
        self.url = mscolab_server
        self.userdata = 'UV10@uv10', 'UV10', 'uv10', 'User UV'
        self.operation_name = "europe"
        with self.app.app_context():
            assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
            assert add_operation(self.operation_name, "test europe")
            assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
            self.user = get_user(self.userdata[0])
        self.window = msui.MSUIMainWindow(local_operations_data=ROOT_DIR)
        self.window.create_new_flight_track()
        self.window.show()
        # connect and login to mscolab
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(self.userdata[0], self.userdata[2])
        # activate operation and open chat window
        self._activate_operation_at_index(0)
        self.window.actionChat.trigger()
        self.chat_window = self.window.mscolab.chat_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.mscolab.logout()
        if self.window.mscolab.chat_window:
            self.window.mscolab.chat_window.hide()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        self.window.hide()

    def test_send_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        with self.app.app_context():
            assert Message.query.filter_by(text='**test message**').count() == 2
            message = Message.query.filter_by(text='**test message**').first()
            result = get_message_dict(message)
            assert result["message_type"] == MessageType.TEXT
            assert datetime.datetime.fromisoformat(result["time"]) == message.created_at

    def test_load_users_with_expired_token_shows_popup(self):
        self.chat_window.token = "expired-token"
        with mock.patch("mslib.msui.mscolab_chat.show_popup") as popup:
            self.chat_window.load_users()
        popup.assert_called_once_with(self.chat_window, "Error", "Session expired, new login required")

    def test_search_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        message_index = self.chat_window.messageList.count() - 1
        # self.window.chat_window.searchMessageLineEdit.setText("test message")
        self.chat_window.searchMessageLineEdit.setText("test message")
        QtTest.QTest.mouseClick(self.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        assert self.chat_window.messageList.item(message_index).isSelected() is True
        QtTest.QTest.mouseClick(self.chat_window.searchPrevBtn, QtCore.Qt.LeftButton)
        assert self.chat_window.messageList.item(message_index - 1).isSelected() is True
        QtTest.QTest.mouseClick(self.chat_window.searchNextBtn, QtCore.Qt.LeftButton)
        assert self.chat_window.messageList.item(message_index).isSelected() is True

    def test_copy_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        self._activate_context_menu_action(Actions.COPY)
        assert QtWidgets.QApplication.clipboard().text() == "**test message**"

    def test_reply_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        parent_message_id = self._get_message_id(self.chat_window.messageList.count() - 1)
        self._activate_context_menu_action(Actions.REPLY)
        self.chat_window.messageText.setPlainText('test reply')
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)

        def assert_():
            with self.app.app_context():
                message = Message.query.filter_by(text='test reply')
                assert message.count() == 1
                assert message.first().reply_id == parent_message_id
        qtbot.wait_until(assert_)

    def test_edit_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        self._activate_context_menu_action(Actions.EDIT)
        self.chat_window.messageText.setPlainText('test edit')
        QtTest.QTest.mouseClick(self.chat_window.editMessageBtn, QtCore.Qt.LeftButton)

        def assert_():
            with self.app.app_context():
                assert Message.query.filter_by(text='test edit').count() == 1
        qtbot.wait_until(assert_)

    def test_delete_message(self, qtbot):
        self._send_message(qtbot, "**test message**")
        self._send_message(qtbot, "**test message**")
        self._activate_context_menu_action(Actions.DELETE)
        with self.app.app_context():
            assert Message.query.filter_by(text='test edit').count() == 0

    def test_events_of_other_operation_ignored(self, qtbot):
        # the socket gets the events of all operations of the user, the chat shows only its own
        self._send_message(qtbot, "own message")
        count = self.chat_window.messageList.count()
        own_id = self._get_message_id(count - 1)
        other_op_id = self.chat_window.op_id + 1000
        foreign = {"id": own_id + 1000, "u_id": self.user.id, "username": self.user.username, "text": "foreign",
                   "message_type": MessageType.TEXT, "reply_id": -1, "replies": [],
                   "time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(), "op_id": other_op_id}
        self.chat_window.handle_incoming_message(json.dumps(foreign))
        self.chat_window.handle_incoming_message_reply(json.dumps(foreign | {"reply_id": own_id}))
        self.chat_window.handle_message_edited(json.dumps(
            {"message_id": own_id, "new_message_text": "foreign edit", "op_id": other_op_id}))
        self.chat_window.handle_deleted_message(json.dumps({"message_id": own_id, "op_id": other_op_id}))
        assert self.chat_window.messageList.count() == count
        widget = self.chat_window.messageList.itemWidget(self.chat_window.messageList.item(count - 1))
        assert widget.message_text == "own message"
        assert widget.replies == []

    def _upload(self, qtbot, file_name, content, message_type):
        num_messages_before = self.chat_window.messageList.count()
        response = requests.post(f"{self.url}/message_attachment",
                                 data={"token": self.window.mscolab.token, "op_id": self.chat_window.op_id,
                                       "message_type": int(message_type)},
                                 files={"file": (file_name, content)}, timeout=10)
        assert response.json()["success"] is True

        def assert_():
            assert self.chat_window.messageList.count() == num_messages_before + 1
        qtbot.wait_until(assert_)
        return self.chat_window.messageList.itemWidget(self.chat_window.messageList.item(num_messages_before))

    def test_image_attachment_fetched_with_token(self, qtbot):
        with open(icons('16x16'), 'rb') as f:
            widget = self._upload(qtbot, "image.png", f.read(), MessageType.IMAGE)
        # /uploads requires the token, without it the server answers "False", which is no image
        assert not widget.message_image.isNull()

    def test_document_link_downloads_with_token(self, qtbot, tmp_path):
        widget = self._upload(qtbot, "notes.txt", b"attached notes", MessageType.DOCUMENT)
        target = tmp_path / "notes.txt"
        with mock.patch("mslib.msui.mscolab_chat.get_save_filename", return_value=str(target)), \
                mock.patch("PyQt5.QtGui.QDesktopServices.openUrl") as open_url:
            widget.on_link_click(QtCore.QUrl(f"{self.url}/{widget.attachment_path}"))
        # a browser has no token, the client downloads the document itself
        open_url.assert_not_called()
        assert target.read_bytes() == b"attached notes"

    @pytest.mark.parametrize("message_type", [MessageType.IMAGE, MessageType.DOCUMENT])
    @pytest.mark.parametrize("text", ["https://attacker.example/x.png", "//attacker.example/x.png",
                                      "http://localhost:1/x.png"])
    def test_foreign_attachment_not_fetched_with_token(self, qtbot, tmp_path, message_type, text):
        # attachment messages of older servers could be edited to point anywhere, the token stays on the server
        message = {"id": 987654, "u_id": self.user.id, "username": self.user.username, "text": text,
                   "message_type": message_type, "reply_id": -1, "replies": [],
                   "time": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                   "op_id": self.chat_window.op_id}
        target = tmp_path / "x.png"
        with mock.patch("mslib.msui.mscolab_chat.requests.get") as get, \
                mock.patch("mslib.msui.mscolab_chat.get_save_filename", return_value=str(target)), \
                mock.patch("mslib.msui.mscolab_chat.show_popup") as popup:
            self.chat_window.handle_incoming_message(json.dumps(message))
            widget = self.chat_window.messageList.itemWidget(
                self.chat_window.messageList.item(self.chat_window.messageList.count() - 1))
            assert widget.attachment_url() is None
            widget.handle_download_action()
        get.assert_not_called()
        if message_type == MessageType.DOCUMENT:
            popup.assert_called_once()
            assert not target.exists()

    def test_refused_document_download_not_saved(self, qtbot, tmp_path):
        widget = self._upload(qtbot, "notes.txt", b"attached notes", MessageType.DOCUMENT)
        target = tmp_path / "notes.txt"
        self.chat_window.token = "invalid"
        with mock.patch("mslib.msui.mscolab_chat.get_save_filename", return_value=str(target)), \
                mock.patch("mslib.msui.mscolab_chat.show_popup") as popup:
            widget.handle_download_action()
        # the server refuses the request, its error page must not be saved as the document
        popup.assert_called_once()
        assert not target.exists()

    def _connect_to_mscolab(self, qtbot):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert not self.connect_window.connectBtn.isVisible()
            assert self.connect_window.disconnectBtn.isVisible()
        qtbot.wait_until(assert_)

    def _login(self, emailid, password):
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)

    def _activate_operation_at_index(self, index):
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)

    def _activate_context_menu_action(self, action_index):
        item = self.chat_window.messageList.item(self.chat_window.messageList.count() - 1)
        message_widget = self.chat_window.messageList.itemWidget(item)
        message_widget.context_menu.actions()[action_index].trigger()

    def _send_message(self, qtbot, text):
        num_messages_before = self.chat_window.messageList.count()
        self.chat_window.messageText.setPlainText(text)
        QtTest.QTest.mouseClick(self.chat_window.sendMessageBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert self.chat_window.messageList.count() == num_messages_before + 1
        qtbot.wait_until(assert_)

    def _get_message_id(self, index):
        item = self.chat_window.messageList.item(index)
        message_widget = self.chat_window.messageList.itemWidget(item)
        return message_widget.id
