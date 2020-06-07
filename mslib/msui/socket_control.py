# -*- coding: utf-8 -*-
"""

    mslib.msui.socket_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    client socket connection handler

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.

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
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default


class ConnectionManager(QtCore.QObject):

    signal_reload = QtCore.Signal(int, name="reload_wps")
    signal_autosave = QtCore.Signal(int, int, name="autosave en/db")
    signal_message_receive = QtCore.Signal(str, str, name="message rcv")
    signal_new_permission = QtCore.Signal(int, int, name="new permission")
    signal_update_permission = QtCore.Signal(int, int, str, name="update permission")
    signal_revoke_permission = QtCore.Signal(int, int, name="revoke permission")
    signal_project_permissions_updated = QtCore.Signal(int, name="project permissions updated")

    def __init__(self, token, user, mscolab_server_url=mss_default.mscolab_server_url):
        super(ConnectionManager, self).__init__()
        self.sio = socketio.Client(reconnection_attempts=5)
        self.sio.on('file-changed', handler=self.handle_file_change)
        # ToDo merge them into one 'autosave-client' event
        self.sio.on('autosave-client-en', handler=self.handle_autosave_enable)
        self.sio.on('autosave-client-db', handler=self.handle_autosave_disable)
        # on chat message recive
        self.sio.on('chat-message-client', handler=self.handle_incoming_message)
        # on new permission
        self.sio.on('new-permission', handler=self.handle_new_permission)
        # on update of permission
        self.sio.on('update-permission', handler=self.handle_update_permission)
        # on revoking project permission
        self.sio.on('revoke-permission', handler=self.handle_revoke_permission)
        # on updating project permissions in admin window
        self.sio.on('project-permissions-updated', handler=self.handle_project_permissions_updated)
        self.mscolab_server_url = mscolab_server_url
        self.sio.connect(self.mscolab_server_url)
        self.sio.emit('start', {'token': token})
        self.token = token
        self.user = user

    def handle_update_permission(self, message):
        """
        signal update of permission affected
        """
        message = json.loads(message)
        p_id = int(message["p_id"])
        u_id = int(message["u_id"])
        access_level = message["access_level"]
        self.signal_update_permission.emit(p_id, u_id, access_level)

    def handle_new_permission(self, message):
        """
        signal updating of newly added permission
        """
        message = json.loads(message)
        p_id = int(message["p_id"])
        u_id = int(message["u_id"])
        self.signal_new_permission.emit(p_id, u_id)

    def handle_revoke_permission(self, message):
        """
        Signal update of revoked permission
        """
        message = json.loads(message)
        p_id = int(message["p_id"])
        u_id = int(message["u_id"])
        self.signal_revoke_permission.emit(p_id, u_id)

    def handle_project_permissions_updated(self, message):
        message = json.loads(message)
        u_id = int(message["u_id"])
        self.signal_project_permissions_updated.emit(u_id)

    def handle_incoming_message(self, message):
        # raise signal to render to view
        message = json.loads(message)
        logging.debug(message)
        # emit signal
        self.signal_message_receive.emit(message["user"], message["message_text"])

    def handle_file_change(self, message):
        message = json.loads(message)
        self.signal_reload.emit(message["p_id"])

    def handle_new_room(self, p_id):
        logging.debug("adding user to new room")
        self.sio.emit('add-user-to-room', {
                      "p_id": p_id,
                      "token": self.token})

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
