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
    signal_autosave = QtCore.Signal(int, int, name="autosave en/db")
    signal_message_receive = QtCore.Signal(str, str, name="message rcv")

    def __init__(self, token, user):
        super(ConnectionManager, self).__init__()
        self.sio = socketio.Client()
        self.sio.on('file-changed', handler=self.handle_file_change)
        # ToDo merge them into one 'autosave-client' event
        self.sio.on('autosave-client-en', handler=self.handle_autosave_enable)
        self.sio.on('autosave-client-db', handler=self.handle_autosave_disable)
        # on chat message recive
        self.sio.on('chat-message-client', handler=self.handle_incoming_message)
        self.sio.connect("http://localhost:8083")
        self.sio.emit('start', {'token': token})
        self.token = token
        self.user = user

    def handle_incoming_message(self, message):
        # raise signal to render to view
        message = json.loads(message)
        logging.debug(message)
        # emit signal
        self.signal_message_receive.emit(message["user"], message["message_text"])

    def handle_file_change(self, message):
        message = json.loads(message)
        self.signal_reload.emit(message["p_id"])

    def send_message(self, message_text, p_id):
        logging.debug("sending message")
        self.sio.emit('chat-message', {
                      "p_id": p_id,
                      "token": self.token,
                      "message_text": message_text})

    def save_file(self, token, p_id, content, comment=None):
        logging.debug("saving file")
        self.sio.emit('file-save', {
                      "p_id": p_id,
                      "token": self.token,
                      "content": content,
                      "comment": comment})

    def emit_autosave(self, token, p_id, enable):
        logging.debug("emitting autosave")
        self.sio.emit('autosave', {
                      "p_id": p_id,
                      "token": token,
                      "enable": enable})

    # ToDo directly call self.signal_autosave

    def handle_autosave_enable(self, message):
        message = json.loads(message)
        self.signal_autosave.emit(1, message["p_id"])

    def handle_autosave_disable(self, message):
        message = json.loads(message)
        self.signal_autosave.emit(0, message["p_id"])

    def disconnect(self):
        self.sio.disconnect()
