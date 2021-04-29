# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat_manager functionalities

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
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
import requests
import json
import sys
import pytest

from werkzeug.urls import url_join
from PyQt5 import QtWidgets, QtTest
from mslib.mscolab.models import User, MessageType, Message
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.chat_manager import ChatManager
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9321, 9340))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Chat_Manager(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(100)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.cm = ChatManager()
        self.room_name = "europe"
        data = {
            'email': 'a',
            'password': 'a'
        }
        r = requests.post(self.url + '/token', data=data)
        self.token = json.loads(r.text)['token']
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

        data = {
            "token": self.token,
            "path": self.room_name,
            "description": "test description"
        }
        url = url_join(self.url, 'create_project')
        requests.post(url, data=data)

    def teardown(self):
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_add_message(self):
        with self.app.app_context():
            message = self.cm.add_message(self.user, 'some message', self.room_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            assert message.text == 'some message'

    def test_edit_messages(self):
        with self.app.app_context():
            message = self.cm.add_message(self.user, 'some test message', self.room_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            new_message_text = "Wonderland"
            self.cm.edit_message(message.id, new_message_text)
            message = Message.query.filter_by(id=message.id).first()
            assert message.text == new_message_text

    def test_delete_messages(self):
        with self.app.app_context():
            message = self.cm.add_message(self.user, 'some test example message',
                                          self.room_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            assert 'some test example message' in message.text
            self.cm.delete_message(message.id)
            message = Message.query.filter(Message.id == message.id).first()
            assert message is None
