# -*- coding: utf-8 -*-
"""

    mslib.msui.socket_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    client socket connection handler

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.

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

from PyQt5 import QtCore
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default


class ConnectionManager(QtCore.QObject):

    signal_reload = QtCore.Signal(int, name="reload_wps")
    signal_message_receive = QtCore.Signal(str, name="message rcv")
    signal_message_reply_receive = QtCore.Signal(str, name="message reply")
    signal_message_edited = QtCore.Signal(str, name="message editted")
    signal_message_deleted = QtCore.Signal(str, name="message deleted")
    signal_new_permission = QtCore.Signal(int, int, name="new permission")
    signal_update_permission = QtCore.Signal(int, int, str, name="update permission")
    signal_revoke_permission = QtCore.Signal(int, int, name="revoke permission")
    signal_project_permissions_updated = QtCore.Signal(int, name="project permissions updated")
    signal_project_deleted = QtCore.Signal(int, name="project deleted")

    def __init__(self, token, user, mscolab_server_url=mss_default.mscolab_server_url):
        super(ConnectionManager, self).__init__()
        self.token = token
        self.user = user
        self.mscolab_server_url = mscolab_server_url
        logging.getLogger("engineio.client").addFilter(filter=lambda record: token not in record.getMessage())
        self.sio = socketio.Client(reconnection_attempts=5)
        self.sio.connect(self.mscolab_server_url)

        self.sio.on('file-changed', handler=self.handle_file_change)
        # on chat message recive
        self.sio.on('chat-message-client', handler=self.handle_incoming_message)
        self.sio.on('chat-message-reply-client', handler=self.handle_incoming_message_reply)
        # on message edit
        self.sio.on('edit-message-client', handler=self.handle_message_edited)
        # on message delete
        self.sio.on('delete-message-client', handler=self.handle_message_deleted)
        # on new permission
        self.sio.on('new-permission', handler=self.handle_new_permission)
        # on update of permission
        self.sio.on('update-permission', handler=self.handle_update_permission)
        # on revoking project permission
        self.sio.on('revoke-permission', handler=self.handle_revoke_permission)
        # on updating project permissions in admin window
        self.sio.on('project-permissions-updated', handler=self.handle_project_permissions_updated)
        # On Project Delete
        self.sio.on('project-deleted', handler=self.handle_project_deleted)

        self.sio.emit('start', {'token': token})

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
        logging.debug(message)
        # emit signal
        self.signal_message_receive.emit(message)

    def handle_incoming_message_reply(self, message):
        self.signal_message_reply_receive.emit(message)

    def handle_message_edited(self, message):
        self.signal_message_edited.emit(message)

    def handle_message_deleted(self, message):
        self.signal_message_deleted.emit(message)

    def handle_file_change(self, message):
        message = json.loads(message)
        self.signal_reload.emit(message["p_id"])

    def handle_project_deleted(self, message):
        p_id = int(json.loads(message)["p_id"])
        self.signal_project_deleted.emit(p_id)

    def handle_new_room(self, p_id):
        logging.debug("adding user to new room")
        self.sio.emit('add-user-to-room', {
                      "p_id": p_id,
                      "token": self.token})

    def send_message(self, message_text, p_id, reply_id):
        logging.debug("sending message")
        self.sio.emit('chat-message', {
                      "p_id": p_id,
                      "token": self.token,
                      "message_text": message_text,
                      "reply_id": reply_id})

    def edit_message(self, message_id, new_message_text, p_id):
        self.sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": new_message_text,
            "p_id": p_id,
            "token": self.token
        })

    def delete_message(self, message_id, p_id):
        self.sio.emit('delete-message', {
            'message_id': message_id,
            'p_id': p_id,
            'token': self.token
        })

    def save_file(self, token, p_id, content, comment=None):
        logging.debug("saving file")
        self.sio.emit('file-save', {
                      "p_id": p_id,
                      "token": self.token,
                      "content": content,
                      "comment": comment})

    def disconnect(self):
        self.sio.disconnect()
