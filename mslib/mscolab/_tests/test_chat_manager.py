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

import requests
import json
from werkzeug.urls import url_join

from mslib.mscolab.models import User, MessageType, Message
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import db, APP, initialize_managers
from mslib.mscolab.utils import get_recent_pid
from mslib.mscolab.chat_manager import ChatManager


class Test_Chat_Manager(object):
    def setup(self):
        self.sockets = []
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, _, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = ChatManager()
        self.room_name = "europe"
        db.init_app(self.app)
        data = {
            'email': 'a',
            'password': 'a'
        }
        r = requests.post(MSCOLAB_URL_TEST + '/token', data=data)
        self.token = json.loads(r.text)['token']
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

        data = {
            "token": self.token,
            "path": self.room_name,
            "description": "test description"
        }
        url = url_join(MSCOLAB_URL_TEST, 'create_project')
        r = requests.post(url, data=data)

    def teardown(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            self.fm.delete_file(p_id, self.user)
            db.session.commit()
        for socket in self.sockets:
            socket.disconnect()

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

    def _login(self):
        url = url_join(MSCOLAB_URL_TEST, 'token')
        r = requests.post(url, data={
            'email': 'mytestuser@test.com',
            'password': 'mx'
        })
        response = json.loads(r.text)
        return response
