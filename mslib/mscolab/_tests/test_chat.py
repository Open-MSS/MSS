# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat functionalities

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
import datetime
import json
import sys
import fs
import requests
import socketio
import pytest

from PyQt5 import QtWidgets, QtTest
from werkzeug.urls import url_join
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message, MessageType
from mslib.msui.icons import icons
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import mscolab_start_server
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.seed import add_user
from flask_testing import TestCase
from mslib.mscolab.sockets_manager import setup_managers
from mslib.mscolab.server import APP
PORTS = list(range(9300, 9320))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Chat(TestCase):
    render_templates = False

    def create_app(self):
        app = APP
        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['LIVESERVER_PORT'] = 0
        return app

    def setup(self):
        handle_db_reset()
        self.socketio, self.cm, self.fm = setup_managers(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.sockets = []
        self.user = get_user(self.userdata[0])

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_send_message(self):
        response = self._login()
        sio = socketio.Client()
        self.sockets.append(sio)
        messages = []

        def handle_incoming_message(msg):
            msg = json.loads(msg)
            messages.append(msg)

        sio.on('chat-message-client', handler=handle_incoming_message)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(2)
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.sleep(2)
        # testing non-ascii message
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "® non ascii",
            "reply_id": -1
        })
        sio.sleep(4)
        assert messages[0]["text"] == "message from 1"
        assert messages[1]["text"] == "® non ascii"
        with self.app.app_context():
            message = Message.query.filter_by(text="message from 1").first()
            assert message.p_id == 1
            assert message.u_id == 8

            message = Message.query.filter_by(text="® non ascii").first()
            assert message is not None

    def test_get_messages(self):
        response = self._login()
        sio = socketio.Client()
        self.sockets.append(sio)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(4)
        # ToDo same message gets twice emmitted, why? (use a helper function)
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "message from 1",
            "reply_id": -1
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
        sio = socketio.Client()
        self.sockets.append(sio)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(2)
        # ToDo same message gets twice emmitted, why?
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.sleep(2)

        token = response["token"]
        data = {
            "token": token,
            "p_id": 1,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
        }
        # returns an array of messages
        url = url_join(self.url, 'messages')
        res = requests.get(url, data=data).json()
        assert len(res["messages"]) == 2

        data["token"] = "dummy"
        # returns False due to bad authorization
        r = requests.get(url, data=data)
        assert r.text == "False"

    def test_edit_message(self):
        response = self._login()
        sio = socketio.Client()
        self.sockets.append(sio)
        edited_messages = []

        def handle_message_edited(msg):
            msg = json.loads(msg)
            edited_messages.append(msg)

        sio.on('edit-message-client', handler=handle_message_edited)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(2)
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "Edit this message",
            "reply_id": -1
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

    def test_delete_message(self):
        response = self._login()
        sio = socketio.Client()
        self.sockets.append(sio)
        deleted_messages = []

        def handle_message_deleted(msg):
            msg = json.loads(msg)
            deleted_messages.append(msg)

        sio.on('delete-message-client', handler=handle_message_deleted)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(2)
        sio.emit("chat-message", {
            "p_id": 1,
            "token": response['token'],
            "message_text": "delete this message",
            "reply_id": -1
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
        self.sockets.append(sio)
        message_recv = []

        def handle_incoming_message(msg):
            msg = json.loads(msg)
            message_recv.append(msg)

        sio.on('chat-message-client', handler=handle_incoming_message)
        sio.connect(self.url)
        sio.emit('start', response)
        sio.sleep(1)
        files = {'file': open(icons('16x16'), 'rb')}
        data = {
            "token": token,
            "p_id": 1,
            "message_type": int(MessageType.IMAGE)
        }
        url = url_join(self.url, 'message_attachment')
        requests.post(url, data=data, files=files)
        sio.sleep(1)
        assert len(message_recv) == 1
        assert fs.path.join("uploads", "1", "mss-logo") in message_recv[0]["text"]

    def _login(self):
        url = url_join(self.url, 'token')
        r = requests.post(url, data={
            'email': self.userdata[0],
            'password': self.userdata[2]
        })
        response = json.loads(r.text)
        return response
