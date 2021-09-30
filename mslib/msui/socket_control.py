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
from mslib.utils.config import MissionSupportSystemDefaultConfig as mss_default
from mslib.mscolab.utils import verify_user_token


class ConnectionManager(QtCore.QObject):

    signal_reload = QtCore.Signal(int, name="reload_wps")
    signal_message_receive = QtCore.Signal(str, name="message rcv")
    signal_message_reply_receive = QtCore.Signal(str, name="message reply")
    signal_message_edited = QtCore.Signal(str, name="message editted")
    signal_message_deleted = QtCore.Signal(str, name="message deleted")
    signal_new_permission = QtCore.Signal(int, int, name="new permission")
    signal_update_permission = QtCore.Signal(int, int, str, name="update permission")
    signal_revoke_permission = QtCore.Signal(int, int, name="revoke permission")
    signal_operation_permissions_updated = QtCore.Signal(int, name="operation permissions updated")
    signal_operation_list_updated = QtCore.Signal(name="operation list updated")
    signal_operation_deleted = QtCore.Signal(int, name="operation deleted")

    def __init__(self, token, user, mscolab_server_url=mss_default.mscolab_server_url):
        super(ConnectionManager, self).__init__()
        self.token = token
        self.user = user
        self.mscolab_server_url = mscolab_server_url
        if token is not None:
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
        # on revoking operation permission
        self.sio.on('revoke-permission', handler=self.handle_revoke_permission)
        # on updating operation permissions in admin window
        self.sio.on('operation-permissions-updated', handler=self.handle_operation_permissions_updated)
        # On Operation Delete
        self.sio.on('operation-deleted', handler=self.handle_operation_deleted)
        # On New Operation
        self.sio.on('operation-list-update', handler=self.handle_operation_list_update)

        self.sio.emit('start', {'token': token})

    def handle_update_permission(self, message):
        """
        signal update of permission affected
        """
        message = json.loads(message)
        op_id = int(message["op_id"])
        u_id = int(message["u_id"])
        access_level = message["access_level"]
        self.signal_update_permission.emit(op_id, u_id, access_level)

    def handle_new_permission(self, message):
        """
        signal updating of newly added permission
        """
        message = json.loads(message)
        op_id = int(message["op_id"])
        u_id = int(message["u_id"])
        self.signal_new_permission.emit(op_id, u_id)

    def handle_revoke_permission(self, message):
        """
        Signal update of revoked permission
        """
        message = json.loads(message)
        op_id = int(message["op_id"])
        u_id = int(message["u_id"])
        self.signal_revoke_permission.emit(op_id, u_id)

    def handle_operation_permissions_updated(self, message):
        message = json.loads(message)
        u_id = int(message["u_id"])
        self.signal_operation_permissions_updated.emit(u_id)

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
        self.signal_reload.emit(message["op_id"])

    def handle_operation_deleted(self, message):
        op_id = int(json.loads(message)["op_id"])
        self.signal_operation_deleted.emit(op_id)

    def handle_operation_list_update(self):
        self.signal_operation_list_updated.emit()

    def handle_new_operation(self, op_id):
        logging.debug("adding user to new operation")
        self.sio.emit('add-user-to-operation', {
                      "op_id": op_id,
                      "token": self.token})

    def send_message(self, message_text, op_id, reply_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            logging.debug("sending message")
            self.sio.emit('chat-message', {
                          "op_id": op_id,
                          "token": self.token,
                          "message_text": message_text,
                          "reply_id": reply_id})
        else:
            # this triggers disconnect
            self.signal_reload.emit(op_id)

    def edit_message(self, message_id, new_message_text, op_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            self.sio.emit('edit-message', {
                "message_id": message_id,
                "new_message_text": new_message_text,
                "op_id": op_id,
                "token": self.token
            })
        else:
            # this triggers disconnect
            self.signal_reload.emit(op_id)

    def delete_message(self, message_id, op_id):
        if verify_user_token(self.mscolab_server_url, self.token):
            self.sio.emit('delete-message', {
                'message_id': message_id,
                'op_id': op_id,
                'token': self.token
            })
        else:
            # this triggers disconnect
            self.signal_reload.emit(op_id)

    def save_file(self, token, op_id, content, comment=None):
        # ToDo refactor API
        if verify_user_token(self.mscolab_server_url, self.token):
            logging.debug("saving file")
            self.sio.emit('file-save', {
                          "op_id": op_id,
                          "token": self.token,
                          "content": content,
                          "comment": comment})
        else:
            # this triggers disconnect
            self.signal_reload.emit(op_id)

    def disconnect(self):
        self.sio.disconnect()
