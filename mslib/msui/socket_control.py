# -*- coding: utf-8 -*-
"""

    mslib.msui.socket_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    client socket connection handler

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.

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

import requests
from urllib.parse import urljoin

from PyQt5 import QtCore
from mslib.msui.mscolab_exceptions import MSColabConnectionError
from mslib.utils.config import MSUIDefaultConfig as mss_default
from mslib.utils.verify_user_token import verify_user_token
from mslib.utils.config import config_loader


class ConnectionManager(QtCore.QObject):

    signal_reload = QtCore.pyqtSignal(int, name="reload_wps")
    signal_message_receive = QtCore.pyqtSignal(str, name="message rcv")
    signal_message_reply_receive = QtCore.pyqtSignal(str, name="message reply")
    signal_message_edited = QtCore.pyqtSignal(str, name="message edited")
    signal_message_deleted = QtCore.pyqtSignal(str, name="message deleted")
    signal_new_permission = QtCore.pyqtSignal(int, int, name="new permission")
    signal_update_permission = QtCore.pyqtSignal(int, int, str, name="update permission")
    signal_revoke_permission = QtCore.pyqtSignal(int, int, name="revoke permission")
    signal_operation_permissions_updated = QtCore.pyqtSignal(int, name="operation permissions updated")
    signal_operation_list_updated = QtCore.pyqtSignal(name="operation list updated")
    signal_operation_deleted = QtCore.pyqtSignal(int, name="operation deleted")
    signal_active_user_update = QtCore.pyqtSignal(int, int)
    signal_update_collaborator_list = QtCore.pyqtSignal()

    def __init__(self, token, user, mscolab_server_url=mss_default.mscolab_server_url):
        super(ConnectionManager, self).__init__()
        self.token = token
        self.user = user
        self.mscolab_server_url = mscolab_server_url
        if token is not None:
            logging.getLogger("engineio.client").addFilter(filter=lambda record: token not in record.getMessage())
        self.sio = socketio.Client(reconnection_attempts=5)
        self.sio.connect(self.mscolab_server_url)
        logging.debug("Transport Layer: %s", self.sio.transport())

        self.sio.on('file-changed', handler=self.handle_file_change)
        # on chat message receive
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
        # On active user update
        self.sio.on('active-user-update', handler=self.handle_active_user_update)

        self.sio.emit('start', {'token': token})

    def handle_active_user_update(self, data):
        """Handle the update for the number of active users on an operation."""
        if isinstance(data, str):
            data = json.loads(data)  # Safely decode in case of string
        op_id = data['op_id']
        count = data['count']
        self.signal_active_user_update.emit(op_id, count)
        self.signal_update_collaborator_list.emit()

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

    def select_operation(self, op_id):
        # Emit an event to notify the server of the operation selection.
        self.sio.emit('operation-selected', {'token': self.token, 'op_id': op_id})

    def save_file(self, token, op_id, content, comment=None, version_name=None, messageText=""):
        # ToDo refactor API
        if verify_user_token(self.mscolab_server_url, self.token):
            logging.debug("saving file")
            self.sio.emit('file-save', {
                          "op_id": op_id,
                          "token": self.token,
                          "content": content,
                          "comment": comment,
                          "version_name": version_name,
                          "messageText": messageText})
        else:
            # this triggers disconnect
            self.signal_reload.emit(op_id)

    def disconnect(self):
        # Get all pyqtSignals defined in this class and disconnect them from all slots
        allSignals = {
            attr
            for attr in dir(self.__class__)
            if isinstance(getattr(self.__class__, attr), QtCore.pyqtSignal)
        }
        inheritedSignals = {
            attr
            for base_class in self.__class__.__bases__
            for attr in dir(base_class)
            if isinstance(getattr(base_class, attr), QtCore.pyqtSignal)
        }
        signals = {getattr(self, signal) for signal in allSignals - inheritedSignals}
        for signal in signals:
            try:
                signal.disconnect()
            except TypeError:
                # The disconnect call can fail if there are no connected slots, so catch that error here
                pass

        self.sio.disconnect()

    def request_post(self, api, data=None, files=None):
        response = requests.post(
            urljoin(self.mscolab_server_url, api),
            data=((data if data is not None else {}) | {"token": self.token}),
            files=files, timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
        return response

    def request_get(self, api, data=None):
        response = requests.get(
            urljoin(self.mscolab_server_url, api),
            data=((data if data is not None else {}) | {"token": self.token}),
            timeout=tuple(config_loader(dataset="MSCOLAB_timeout")))
        if response.status_code != 200:
            raise MSColabConnectionError
        return response
