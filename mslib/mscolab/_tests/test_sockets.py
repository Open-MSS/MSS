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
from flask import Flask
import socketio
from socketIO_client import SocketIO
from functools import partial
import requests
import threading
import time
import json

from mslib.mscolab.server import db, check_login, register_user, sockio
from conf import SQLALCHEMY_DB_URI


class Test_Sockets(object):
    total = [0, 0, 0]
    def setup(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        self.app.config['SECRET_KEY'] = 'secret!'
        db.init_app(self.app)
        # thread = threading.Thread(target=socketio.run, args=(self.app,))
        # time.sleep(5)


    # def test_connect(self):
    #     # with self.app.app_context():
    #     r = requests.post("http://localhost:5000/token", data={
    #                       'emailid': 'a',
    #                       'password': 'a'
    #                      })
    #     response = json.loads(r.text)
    #     print(response)
    #     with SocketIO('localhost', 5000) as socketIO:
    #         socketIO.emit('start_event', response)
    #         socketIO.wait(seconds=5)
    #         print("Hi there, im connected")
    
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
            self.total[sno-1] += 1
            print('chat', sno)


        socketIO1 = SocketIO('localhost', 5000)
        socketIO2 = SocketIO('localhost', 5000)
        socketIO3 = SocketIO('localhost', 5000)
        
        socketIO1.emit('start_event', response1)
        socketIO2.emit('start_event', response2)
        socketIO3.emit('start_event', response3)

        socketIO1.on('chat message', partial(handle_chat_message, 1))
        socketIO2.on('chat message', partial(handle_chat_message, 2))
        socketIO3.on('chat message', partial(handle_chat_message, 3))
        print('emitting message now')
        socketIO1.emit('emit-message', {
                       "p_id": 1,
                       "token": response1['token']
                    })
        socketIO1.wait(1)
        socketIO2.wait(1)
        socketIO3.wait(1)
        socketIO3.emit('emit-message', {
                       "p_id": 1,
                       "token": response3['token']
                    })
        
        socketIO1.wait(1)
        socketIO2.wait(1)
        socketIO3.wait(1)
        socketIO3.emit('emit-message', {
                       "p_id": 3,
                       "token": response3['token']
                    })
        
        socketIO1.wait(1)
        socketIO2.wait(1)
        socketIO3.wait(1)

        assert self.total[0] == 2
        assert self.total[1] == 1
        assert self.total[2] == 2

    

    def teardown(self):
        pass
