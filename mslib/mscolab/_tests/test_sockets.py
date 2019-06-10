# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_user.py
    ~~~~~~~~~~~~~~~~~~~~

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
import os


class Test_Sockets(object):
    total = [0, 0, 0]

    def setup(self):
        self.sockets = []
        cwd = os.getcwd()
        path_to_server = cwd + "/mslib/mscolab/server.py"
        subprocess.Popen(["python", path_to_server], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        time.sleep(4)

    def test_connect(self):
        r = requests.post("http://localhost:5000/token", data={
                          'emailid': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        # standard Python
        sio = socketio.Client()

        sio.connect('http://localhost:5000')
        sio.emit('start_event', response)
        sio.sleep(2)
        self.sockets.append(sio)

    def test_emit_permissions(self):
        r = requests.post("http://localhost:5000/token", data={
                          'emailid': 'a',
                          'password': 'a'
                          })
        response1 = json.loads(r.text)
        r = requests.post("http://localhost:5000/token", data={
                          'emailid': 'b',
                          'password': 'b'
                          })
        response2 = json.loads(r.text)
        r = requests.post("http://localhost:5000/token", data={
                          'emailid': 'c',
                          'password': 'c'
                          })
        response3 = json.loads(r.text)

        def handle_chat_message(sno, message):
            self.total[sno - 1] += 1

        sio1 = socketio.Client()
        sio2 = socketio.Client()
        sio3 = socketio.Client()

        sio1.on('chat message', handler=partial(handle_chat_message, 1))
        sio2.on('chat message', handler=partial(handle_chat_message, 2))
        sio3.on('chat message', handler=partial(handle_chat_message, 3))
        sio1.connect('http://localhost:5000')
        sio2.connect('http://localhost:5000')
        sio3.connect('http://localhost:5000')

        sio1.emit('start_event', response1)
        sio2.emit('start_event', response2)
        sio3.emit('start_event', response3)
        time.sleep(5)
        sio1.emit('emit-message', {
                  "p_id": 1,
                  "token": response1['token']
                  })

        sio3.emit('emit-message', {
                  "p_id": 1,
                  "token": response3['token']
                  })

        sio3.emit('emit-message', {
                  "p_id": 3,
                  "token": response3['token']
                  })

        sio1.sleep(1)
        sio2.sleep(1)
        sio3.sleep(1)

        assert self.total[0] == 2
        assert self.total[1] == 1
        assert self.total[2] == 2
        self.sockets.append(sio1)
        self.sockets.append(sio2)
        self.sockets.append(sio3)

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        subprocess.run(["fuser", "-k", "5000/tcp"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        pass
