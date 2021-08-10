# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat_manager functionalities

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
from flask import Flask
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, MessageType, Message
from mslib.mscolab.chat_manager import ChatManager
from mslib.mscolab.seed import add_user, add_project, add_user_to_project, delete_user, delete_project, get_user
from mslib.mscolab.mscolab import handle_db_seed


class Test_Chat_Manager(object):
    def setup(self):
        handle_db_seed()
        self.app = Flask(__name__, static_url_path='')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        self.cm = ChatManager()

        self.room_name = "europe"
        self.userdata = "va6@v6", "va6", "va6"

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, "test europe")
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])

    def teardown(self):
        assert delete_user(self.userdata[0])
        assert delete_project(self.room_name)

    def test_add_message(self):
        with self.app.app_context():

            message = self.cm.add_message(self.user, 'some message',
                                          self.room_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            assert message.text == 'some message'

    def test_edit_messages(self):
        with self.app.app_context():
            message = self.cm.add_message(self.user, 'some test message',
                                          self.room_name, message_type=MessageType.TEXT,
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
