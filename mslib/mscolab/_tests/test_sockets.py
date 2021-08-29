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
import pytest
import socketio

from mslib.mscolab.conf import mscolab_settings
from mslib._tests.utils import mscolab_check_free_port, LiveSocketTestCase
from mslib.mscolab.server import db, APP, initialize_managers
from mslib.mscolab.seed import add_user, get_user, add_project, add_user_to_project, get_project
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.sockets_manager import SocketsManager
from mslib.mscolab.models import Permission, User

PORTS = list(range(9521, 9540))


class Test_Sockets(LiveSocketTestCase):
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
        self._process.terminate()

    def _connect(self):
        sio = socketio.Client()
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

    def test_chat_message_emit(self):
        sio = socketio.Client()
        assert self.chat_messages_counter_a == 0

        def handle_chat_message(message):
            self.chat_messages_counter_a += 1

        sio.on('chat-message-client', handler=handle_chat_message)
        sio.connect(self.url)
        sio.emit('connect')
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {"p_id": self.project.id, "token": self.token,
                                  "message_text": "message from 1", "reply_id": -1}
                 )
        sio.sleep(1)
        assert self.chat_messages_counter_a == 1
        sio.emit("chat-message", {"p_id": self.project.id, "token": self.token,
                                  "message_text": "message from 1", "reply_id": -1}
                 )
        sio.sleep(1)
        assert self.chat_messages_counter_a == 2
