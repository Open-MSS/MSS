# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat functionalities

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
import datetime
import json

import fs
import requests
import socketio
from werkzeug.urls import url_join

from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message, MessageType
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.icons import icons


class Test_Chat(object):

    def setup(self):
        self.sockets = []
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app, _, cm, _ = initialize_managers(self.app)
        self.cm = cm
        db.init_app(self.app)

    def test_send_message(self):
        response = self._login()
        sio = socketio.Client()
        messages = []

        def handle_incoming_message(msg):
            msg = json.loads(msg)
            messages.append(msg)

        sio.on('chat-message-client', handler=handle_incoming_message)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.sleep(2)
        # testing non-ascii message
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "® non ascii"
                 })
        sio.sleep(2)
        assert messages[0]["text"] == "message from 1"
        assert messages[1]["text"] == "® non ascii"
        with self.app.app_context():
            message = Message.query.filter_by(text="message from 1").first()
            assert message.p_id == 1
            assert message.u_id == 8

            message = Message.query.filter_by(text="® non ascii").first()
            assert message is not None
            Message.query.filter_by(text="message from 1").delete()
            Message.query.filter_by(text="® non ascii").delete()
            db.session.commit()

    def test_get_messages(self):
        response = self._login()
        sio = socketio.Client()
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.sleep(2)
        with self.app.app_context():
            messages = self.cm.get_messages(1)
            assert messages[0]["text"] == "message from 1"
            assert len(messages) == 2
            assert messages[0]["u_id"] == 8
            timestamp = datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 2
            assert messages[0]["u_id"] == 8
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 0

    def test_get_messages_api(self):
        response = self._login()
        token = response["token"]
        data = {
            "token": token,
            "p_id": 1,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
        }
        # returns an array of messages
        url = url_join(MSCOLAB_URL_TEST, 'messages')
        res = requests.get(url, data=data).json()
        assert len(res["messages"]) == 2

        data["token"] = "dummy"
        # returns False due to bad authorization
        r = requests.get(url, data=data)
        assert r.text == "False"
        with self.app.app_context():
            Message.query.filter_by(text="message from 1").delete()
            db.session.commit()

    def test_edit_message(self):
        response = self._login()
        sio = socketio.Client()
        edited_messages = []

        def handle_message_edited(msg):
            msg = json.loads(msg)
            edited_messages.append(msg)

        sio.on('edit-message-client', handler=handle_message_edited)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "Edit this message"
                 })
        sio.sleep(2)
        with self.app.app_context():
            message = Message.query.filter_by(text="Edit this message").first()
        sio.emit('edit-message', {
            "message_id": message.id,
            "new_message_text": "I have updated the message",
            "p_id": message.p_id,
            "token": response["token"]
        })
        sio.sleep(2)
        assert len(edited_messages) == 1
        assert edited_messages[0]["new_message_text"] == "I have updated the message"
        with self.app.app_context():
            edited_message = Message.query.filter_by(text="I have updated the message").first()
            assert edited_message.id == message.id
            db.session.delete(edited_message)
            db.session.commit()

    def test_delete_message(self):
        response = self._login()
        sio = socketio.Client()
        deleted_messages = []

        def handle_message_deleted(msg):
            msg = json.loads(msg)
            deleted_messages.append(msg)

        sio.on('delete-message-client', handler=handle_message_deleted)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "delete this message"
        })
        sio.sleep(2)
        with self.app.app_context():
            message = Message.query.filter_by(text="delete this message").first()
        sio.emit('delete-message', {
            'message_id': message.id,
            'p_id': 1,
            'token': response["token"]
        })
        sio.sleep(2)
        assert len(deleted_messages) == 1
        assert deleted_messages[0]["message_id"] == message.id
        with self.app.app_context():
            assert Message.query.filter_by(text="delete this message").count() == 0

    def test_upload_file(self):
        response = self._login()
        token = response["token"]
        sio = socketio.Client()
        message_recv = []

        def handle_incoming_message(msg):
            msg = json.loads(msg)
            message_recv.append(msg)

        sio.on('chat-message-client', handler=handle_incoming_message)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        files = {'file': open(icons('16x16'), 'rb')}
        data = {
            "token": token,
            "p_id": 1,
            "message_type": int(MessageType.IMAGE)
        }
        url = url_join(MSCOLAB_URL_TEST, 'message_attachment')
        requests.post(url, data=data, files=files)
        sio.sleep(2)
        assert len(message_recv) == 1
        assert fs.path.join("uploads", "1", "mss-logo") in message_recv[0]["text"]

    def _login(self):
        url = url_join(MSCOLAB_URL_TEST, 'token')
        r = requests.post(url, data={
            'email': 'a',
            'password': 'a'
        })
        response = json.loads(r.text)
        return response

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
