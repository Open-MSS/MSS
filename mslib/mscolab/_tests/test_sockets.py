# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_sockets.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for sockets module

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
import multiprocessing
import socketio
from functools import partial
import requests
import json
import time

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message, Project
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.server import db, APP, initialize_managers, start_server
from mslib.mscolab.seed import add_user, get_user, add_project, add_user_to_project, get_project
from mslib.mscolab.mscolab import handle_db_reset

def start_mscolab_server(port):
    """
    testserver
    """
    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
    _app, sockio, cm, fm = initialize_managers(_app)
    process = multiprocessing.Process(
        target=start_server,
        args=(_app, sockio, cm, fm,),
        kwargs={'port': port})
    process.start()
    time.sleep(2)
    return process

class Test_Sockets(object):
    chat_messages_counter = [0, 0, 0]  # three sockets connected a, b, and c
    chat_messages_counter_a = 0  # only for first test

    def setup(self):
        handle_db_reset()
        self.process = start_mscolab_server(8084)
        self.sockets = []
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, cm, _ = initialize_managers(self.app)
        self.cm = cm
        db.init_app(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        self.room_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, "test europe")
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])
        self.token = self.user.generate_auth_token()
        self.project = get_project(self.room_name)

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        self.process.terminate()

    def test_chat_message_emit(self):
        sio = socketio.Client()
        def handle_chat_message(message):
            self.chat_messages_counter_a += 1

        sio.on('chat-message-client', handler=handle_chat_message)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', {'token': self.token})
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
            "p_id": self.project.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })
        sio.sleep(2)
        assert self.chat_messages_counter_a == 1

