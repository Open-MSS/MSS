# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_sockets.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for sockets module

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
import socketio
from functools import partial
import requests
import subprocess
import json
import time
import logging
import os
from flask import Flask

from mslib.mscolab.conf import START_SERVER_DURING_TEST, SQLALCHEMY_DB_URI
from mslib.mscolab.models import db, Message


class Test_Sockets(object):
    chat_messages_counter = [0, 0, 0]  # three sockets connected a, b, and c
    chat_messages_counter_a = 0  # only for first test

    def setup(self):
        self.sockets = []
        cwd = os.getcwd()
        path_to_server = cwd + "/mslib/mscolab/server.py"
        if START_SERVER_DURING_TEST:
            self.proc = subprocess.Popen(["python", path_to_server], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
            try:
                outs, errs = self.proc.communicate(timeout=4)
                print(outs, errs)
            except Exception as e:
                logging.debug("Server isn't running")
                logging.debug(e)
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        self.app.config['SECRET_KEY'] = 'secret!'
        db.init_app(self.app)

    def test_connect(self):
        r = requests.post("http://localhost:8083/token", data={
                          'emailid': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        # standard Python
        sio = socketio.Client()

        def handle_chat_message(message):
            self.chat_messages_counter_a += 1

        sio.on('chat-message-client', handler=handle_chat_message)
        sio.connect('http://localhost:8083')
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.sleep(2)
        assert self.chat_messages_counter_a == 1

    def test_emit_permissions(self):
        r = requests.post("http://localhost:8083/token", data={
                          'emailid': 'a',
                          'password': 'a'
                          })
        response1 = json.loads(r.text)
        r = requests.post("http://localhost:8083/token", data={
                          'emailid': 'b',
                          'password': 'b'
                          })
        response2 = json.loads(r.text)
        r = requests.post("http://localhost:8083/token", data={
                          'emailid': 'c',
                          'password': 'c'
                          })
        response3 = json.loads(r.text)

        def handle_chat_message(sno, message):
            self.chat_messages_counter[sno - 1] += 1

        sio1 = socketio.Client()
        sio2 = socketio.Client()
        sio3 = socketio.Client()

        sio1.on('chat-message-client', handler=partial(handle_chat_message, 1))
        sio2.on('chat-message-client', handler=partial(handle_chat_message, 2))
        sio3.on('chat-message-client', handler=partial(handle_chat_message, 3))
        sio1.connect('http://localhost:8083')
        sio2.connect('http://localhost:8083')
        sio3.connect('http://localhost:8083')

        sio1.emit('start', response1)
        sio2.emit('start', response2)
        sio3.emit('start', response3)
        time.sleep(5)
        sio1.emit('chat-message', {
                  "p_id": 1,
                  "token": response1['token'],
                  "message_text": "message from 1"
                  })

        sio3.emit('chat-message', {
                  "p_id": 1,
                  "token": response3['token'],
                  "message_text": "message from 3 - 1"
                  })

        sio3.emit('chat-message', {
                  "p_id": 3,
                  "token": response3['token'],
                  "message_text": "message from 3 - 2"
                  })

        sio1.sleep(1)
        sio2.sleep(1)
        sio3.sleep(1)

        assert self.chat_messages_counter[0] == 2
        assert self.chat_messages_counter[1] == 1
        assert self.chat_messages_counter[2] == 2
        self.sockets.append(sio1)
        self.sockets.append(sio2)
        self.sockets.append(sio3)

        with self.app.app_context():
            Message.query.filter_by(text="message from 1").delete()
            Message.query.filter_by(text="message from 3 - 1").delete()
            Message.query.filter_by(text="message from 3 - 2").delete()
            db.session.commit()

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        if START_SERVER_DURING_TEST:
            self.proc.kill()
