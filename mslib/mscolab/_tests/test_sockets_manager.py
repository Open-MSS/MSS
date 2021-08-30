# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_sockets.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for sockets module

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
import pytest
import socketio
import datetime
import requests

from werkzeug.urls import url_join
from mslib.msui.icons import icons
from mslib.mscolab.conf import mscolab_settings
from mslib._tests.utils import mscolab_check_free_port, LiveSocketTestCase
from mslib.mscolab.server import db, APP, initialize_managers
from mslib.mscolab.seed import add_user, get_user, add_project, add_user_to_project, get_project
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.sockets_manager import SocketsManager
from mslib.mscolab.models import Permission, User, Message, MessageType

PORTS = list(range(39021, 39540))


@pytest.mark.skip("skipped for now")
class Test_Socket_Manager(LiveSocketTestCase):
    run_gc_after_test = True
    chat_messages_counter = [0, 0, 0]  # three sockets connected a, b, and c
    chat_messages_counter_a = 0  # only for first test

    def create_app(self):
        app = APP
        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 1
        app.config['LIVESERVER_PORT'] = mscolab_check_free_port(PORTS, PORTS.pop())
        return app

    def setUp(self):
        handle_db_reset()
        self.sockets = []
        # self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, self.cm, self.fm = initialize_managers(self.app)
        db.init_app(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        self.room_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, "test europe")
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])
        assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2])
        self.anotheruser = get_user(self.anotheruserdata[0])
        self.token = self.user.generate_auth_token()
        self.project = get_project(self.room_name)
        self.url = self.get_server_url()
        self.sm = SocketsManager(self.cm, self.fm)

    def tearDown(self):
        for socket in self.sockets:
            socket.disconnect()

    def _connect(self):
        sio = socketio.Client(reconnection_attempts=5)
        self.sockets.append(sio)
        assert self._can_ping_server()
        sio.connect(self.url)
        sio.emit('connect')
        return sio

    def _new_room(self, room_name, description):
        assert add_project(room_name, description)
        project = get_project(room_name)
        return project

    def test_handle_connect(self):
        sio = socketio.Client()
        assert sio.sid is None
        self.sockets.append(sio)
        assert self._can_ping_server()
        sio.connect(self.url)
        sio.emit('connect')
        assert len(sio.sid) > 5

    def test_join_creator_to_room(self):
        sio = self._connect()
        project = self._new_room('new_room', "example decription")
        assert self.fm.get_file(int(project.id), self.user) is False
        json_config = {"token": self.token,
                       "p_id": project.id}

        sio.emit('add-user-to-room', json_config)
        perms = Permission(self.user.id, project.id, "creator")
        assert perms.p_id == project.id
        assert perms.u_id == self.user.id
        assert perms.access_level == "creator"

    def test_join_collaborator_to_room(self):
        self._connect()
        project = self._new_room('new_room', "example decription")
        sm = SocketsManager(self.cm, self.fm)
        sm.join_collaborator_to_room(self.anotheruser.id, project.id)
        perms = Permission(self.anotheruser.id, project.id, "collaborator")
        assert perms.p_id == project.id
        assert perms.u_id == self.anotheruser.id
        assert perms.access_level == "collaborator"

    def test_remove_collaborator_from_room(self):
        pytest.skip("get_session_id has None result")
        sio = self._connect()
        project = self._new_room('new_room', "example decription")
        sm = SocketsManager(self.cm, self.fm)
        sm.join_collaborator_to_room(self.anotheruser.id, project.id)
        perms = Permission(self.anotheruser.id, project.id, "collaborator")
        assert perms is not None
        sm.remove_collaborator_from_room(self.anotheruser.id, project.id)
        sio.sleep(1)
        perms = Permission(self.anotheruser.id, project.id, "collaborator")
        assert perms is None

    def test_handle_start_event(self):
        pytest.skip("unknown how to verify")
        sio = self._connect()
        json_config = {"token": self.token}
        assert User.verify_auth_token(self.token) is not False
        sio.emit('start', json_config)

    def test_send_message(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })

        # testing non-ascii message
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "® non ascii",
            "reply_id": -1
        })
        sio.sleep(1)

        with self.app.app_context():
            message = Message.query.filter_by(text="message from 1").first()
            assert message.p_id == self.project.id
            assert message.u_id == self.user.id

            message = Message.query.filter_by(text="® non ascii").first()
            assert message is not None

    def test_get_messages(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        # ToDo same message gets twice emmitted, why? (use a helper function)
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.sleep(1)
        with self.app.app_context():
            messages = self.cm.get_messages(1)
            assert messages[0]["text"] == "message from 1"
            assert len(messages) == 2
            assert messages[0]["u_id"] == self.user.id
            timestamp = datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 2
            assert messages[0]["u_id"] == self.user.id
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 0

    def test_get_messages_api(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})
        # ToDo same message gets twice emmitted, why?
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.sleep(1)

        token = self.token
        data = {
            "token": token,
            "p_id": self.project.id,
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
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "Edit this message",
            "reply_id": -1
        })
        sio.sleep(1)
        with self.app.app_context():
            message = Message.query.filter_by(text="Edit this message").first()
        sio.emit('edit-message', {
            "message_id": message.id,
            "new_message_text": "I have updated the message",
            "p_id": message.p_id,
            "token": self.token
        })
        sio.sleep(1)
        token = self.token
        data = {
            "token": token,
            "p_id": self.project.id,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%Y-%m-%d, %H:%M:%S")
        }
        # returns an array of messages
        url = url_join(self.url, 'messages')
        res = requests.get(url, data=data).json()
        assert len(res["messages"]) == 1
        messages = res["messages"][0]
        assert messages["text"] == "I have updated the message"

    def test_delete_message(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "delete this message",
            "reply_id": -1
        })
        sio.sleep(1)
        with self.app.app_context():
            message = Message.query.filter_by(text="delete this message").first()
        sio.emit('delete-message', {
            'message_id': message.id,
            'p_id': self.project.id,
            'token': self.token
        })
        sio.sleep(1)

        with self.app.app_context():
            assert Message.query.filter_by(text="delete this message").count() == 0

    def test_upload_file(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})
        files = {'file': open(icons('16x16'), 'rb')}
        data = {
            "token": self.token,
            "p_id": self.project.id,
            "message_type": int(MessageType.IMAGE)
        }
        url = url_join(self.url, 'message_attachment')
        requests.post(url, data=data, files=files)
        upload_dir = os.path.join(mscolab_settings.UPLOAD_FOLDER, str(self.user.id))
        assert os.path.exists(upload_dir)
        file = os.listdir(upload_dir)[0]
        assert 'mss-logo' in file
        assert 'png' in file
