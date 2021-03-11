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
import socketio
from functools import partial
import requests
import json
import sys
import time

from PyQt5 import QtWidgets
from mslib.mscolab.conf import mscolab_settings
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9521, 9540))


class Test_Sockets(object):
    chat_messages_counter = [0, 0, 0]  # three sockets connected a, b, and c
    chat_messages_counter_a = 0  # only for first test

    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.1)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.sockets = []

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_connect(self):
        r = requests.post(self.url + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        sio = socketio.Client()
        self.sockets.append(sio)

        def handle_chat_message(message):
            self.chat_messages_counter_a += 1

        sio.on('chat-message-client', handler=handle_chat_message)
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
        assert self.chat_messages_counter_a == 1

    def test_emit_permissions(self):
        r = requests.post(self.url + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response1 = json.loads(r.text)
        r = requests.post(self.url + "/token", data={
                          'email': 'b',
                          'password': 'b'
                          })
        response2 = json.loads(r.text)
        r = requests.post(self.url + "/token", data={
                          'email': 'c',
                          'password': 'c'
                          })
        response3 = json.loads(r.text)

        def handle_chat_message(sno, message):
            self.chat_messages_counter[sno - 1] += 1

        sio1 = socketio.Client()
        sio2 = socketio.Client()
        sio3 = socketio.Client()
        self.sockets.append(sio1)
        self.sockets.append(sio2)
        self.sockets.append(sio3)

        sio1.on('chat-message-client', handler=partial(handle_chat_message, 1))
        sio2.on('chat-message-client', handler=partial(handle_chat_message, 2))
        sio3.on('chat-message-client', handler=partial(handle_chat_message, 3))
        sio1.connect(self.url)
        sio2.connect(self.url)
        sio3.connect(self.url)

        sio1.emit('start', response1)
        sio2.emit('start', response2)
        sio3.emit('start', response3)
        time.sleep(0.1)
        sio1.emit('chat-message', {
            "p_id": 1,
            "token": response1['token'],
            "message_text": "message from 1",
            "reply_id": -1
        })

        sio3.emit('chat-message', {
            "p_id": 1,
            "token": response3['token'],
            "message_text": "message from 3 - 1",
            "reply_id": -1
        })

        sio3.emit('chat-message', {
            "p_id": 3,
            "token": response3['token'],
            "message_text": "message from 3 - 2",
            "reply_id": -1
        })

        sio1.sleep(1)
        sio2.sleep(1)
        sio3.sleep(1)

        assert self.chat_messages_counter[0] == 2
        assert self.chat_messages_counter[1] == 1
        assert self.chat_messages_counter[2] == 2
