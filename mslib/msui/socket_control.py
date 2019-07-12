# -*- coding: utf-8 -*-
"""

    mslib.msui.socket_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    client socket connection handler

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi

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
import json
import logging

from mslib.msui.mss_qt import QtCore


class ConnectionManager(QtCore.QObject):

    signal_reload = QtCore.Signal(int, name="reload_wps")

    def __init__(self, token, user):
        super(ConnectionManager, self).__init__()
        self.sio = socketio.Client()
        self.sio.on('file-changed', handler=self.handle_file_change)
        self.sio.connect("http://localhost:8083")
        self.sio.emit('start', {'token': token})
        self.token = token
        self.user = user

    def handle_file_change(self, message):
        message = json.loads(message)
        self.signal_reload.emit(message["p_id"])

    def send_message(self, channel, message):
        logging.debug("sending message")

    def save_file(self, token, p_id, content):
        logging.debug("saving file")
        self.sio.emit('file-save', {
                      "p_id": p_id,
                      "token": self.token,
                      "content": content})

    def disconnect(self):
        self.sio.disconnect()
