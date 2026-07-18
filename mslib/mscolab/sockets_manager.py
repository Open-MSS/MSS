# -*- coding: utf-8 -*-
"""

    mslib.mscolab.sockets_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
import json
import logging
from flask import request
from flask_socketio import SocketIO, join_room

from mslib.mscolab.chat_manager import ChatManager
from mslib.mscolab.events import SocketEvents
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.models import MessageType, Permission, User
from mslib.mscolab.utils import get_message_dict
from mslib.mscolab.utils import get_user_id
from mslib.mscolab.app import APP

# async_handlers=False handles each client's events in the order they were received. With
# the default (async_handlers=True) every event runs in its own thread, so two rapid
# file-save events can give a wrong final document data.
socketio = SocketIO(logger=APP.config['SOCKETIO_LOGGER'], engineio_logger=APP.config['ENGINEIO_LOGGER'],
                    async_mode='threading',
                    async_handlers=False,
                    cors_allowed_origins=("*" if not hasattr(APP, "CORS_ORIGINS") or
                    "*" in APP.config['CORS_ORIGINS'] else APP.config['CORS_ORIGINS']))


class SocketsManager:
    """Class with handler functions for socket related"""

    def __init__(self, chat_manager, file_manager):
        """
        chat_manager: Instance of ChatManager
        file_manager: Instance of FileManager
        """
        super(SocketsManager, self).__init__()
        self.sockets = []
        self.active_users_per_operation = {}
        self.cm = chat_manager
        self.fm = file_manager

    def handle_connect(self):
        logging.debug(request.sid)

    def clear_state(self):
        """Drop all in-memory socket bookkeeping.

        Called by handle_db_reset so a database reset also discards these registries,
        which would otherwise reference user/operation rows that no longer exist.
        """
        self.sockets[:] = []
        self.active_users_per_operation.clear()

    def handle_operation_selected(self, json_config):
        logging.debug("Operation selected: {}".format(json_config))
        token = json_config['token']
        op_id = json_config['op_id']
        user = User.verify_auth_token(token)
        if user is None:
            return

        # Remove the active user_id from any other operations first
        self.update_active_users(user.id)

        # Add the user to the new operation
        if op_id not in self.active_users_per_operation:
            self.active_users_per_operation[op_id] = set()
        self.active_users_per_operation[op_id].add(user.id)

        # Emit the updated count to all users
        active_count = len(self.active_users_per_operation[op_id])
        socketio.emit(SocketEvents.ACTIVE_USER_UPDATE, {'op_id': op_id, 'count': active_count})

    def update_operation_list(self, json_config):
        """
        json_config has:
        - token: authentication token
        """
        token = json_config["token"]
        user = User.verify_auth_token(token)
        if user is None:
            return
        socketio.emit(SocketEvents.UPDATE_OPERATION_LIST)

    def join_creator_to_operation(self, json_config):
        """
        json_config has:
            - token: authentication token
            - op_id: operation id
        """
        token = json_config['token']
        user = User.verify_auth_token(token)
        if user is None:
            return
        op_id = json_config['op_id']
        join_room(str(op_id))

    def handle_start_event(self, json_config):
        """
        json is a dictionary version of data sent to backend
        """
        logging.info('received json: ' + str(json_config))
        # authenticate socket
        token = json_config['token']
        user = User.verify_auth_token(token)
        if user is None:
            return

        # fetch operations
        permissions = Permission.query.filter_by(u_id=user.id).all()

        # for all the op_id in permissions, there'd be chatrooms in self.rooms
        # search and add user to respective rooms
        for permission in permissions:
            # for each operation with op_id, search rooms
            # socketio.join_room(room, sid=None, namespace=None)
            """
            - a client is always registered as a room with name equal to
            the session id of the client.
            - so the rooms can safely be named as stringified versions of
            the operation id.
            - thus, an abstraction is unnecessary. if it will be, it'll be
            considered during later developments.
            - so joining the actual socketio room would be enough
            """
            join_room(str(permission.op_id))
        socket_storage = {
            's_id': request.sid,
            'u_id': user.id
        }
        self.sockets.append(socket_storage)

    def handle_disconnect(self):
        logging.debug("Handling disconnect.")

        # remove the user from any active operations
        user_id = get_user_id(self.sockets, request.sid)
        if user_id:
            self.update_active_users(user_id)

        logging.debug(f"Disconnected: {request.sid}")
        # remove socket from socket_storage
        self.sockets[:] = [d for d in self.sockets if d['s_id'] != request.sid]

    def update_active_users(self, user_id):
        """
        Remove the given user_id from all operations and emit updates for active user counts.
        """
        for op_id, user_ids in list(self.active_users_per_operation.items()):
            if user_id in user_ids:
                user_ids.remove(user_id)
                active_count = len(user_ids)
                logging.debug(f"Updated {op_id}: {active_count} active users")
                if user_ids:
                    # Emit update if there are still active users
                    socketio.emit(SocketEvents.ACTIVE_USER_UPDATE, {'op_id': op_id, 'count': active_count})
                else:
                    # If no users left, delete the operation key
                    del self.active_users_per_operation[op_id]
                    socketio.emit(SocketEvents.ACTIVE_USER_UPDATE, {'op_id': op_id, 'count': 0})

    def remove_active_user_id_from_specific_operation(self, user_id, op_id):
        """
        Remove the given user_id from a specific operation in active_users_per_operation
        and emit updates for active user counts.
        """
        if op_id in self.active_users_per_operation:
            if user_id in self.active_users_per_operation[op_id]:
                self.active_users_per_operation[op_id].remove(user_id)
                active_count = len(self.active_users_per_operation[op_id])

                if self.active_users_per_operation[op_id]:
                    # Emit update if there are still active users
                    socketio.emit(SocketEvents.ACTIVE_USER_UPDATE, {'op_id': op_id, 'count': active_count})
                else:
                    # If no users left, delete the operation key
                    del self.active_users_per_operation[op_id]
                    socketio.emit(SocketEvents.ACTIVE_USER_UPDATE, {'op_id': op_id, 'count': 0})

    def handle_message(self, _json):
        """
        json is a dictionary version of data sent to back-end
        """
        op_id = _json['op_id']
        reply_id = int(_json["reply_id"])
        user = User.verify_auth_token(_json['token'])
        if user is not None:
            perm = self.permission_check_emit(user.id, int(op_id))
            if perm:
                new_message = self.cm.add_message(user, _json['message_text'], str(op_id), reply_id=reply_id)
                new_message_dict = get_message_dict(new_message)
                if reply_id == -1:
                    socketio.emit(SocketEvents.CHAT_MESSAGE_CLIENT, json.dumps(new_message_dict))
                else:
                    socketio.emit(SocketEvents.CHAT_MESSAGE_REPLY_CLIENT, json.dumps(new_message_dict))

    def handle_message_edit(self, socket_message):
        message_id = socket_message["message_id"]
        op_id = socket_message["op_id"]
        new_message_text = socket_message["new_message_text"]
        user = User.verify_auth_token(socket_message["token"])
        if user is not None:
            perm = self.permission_check_emit(user.id, int(op_id))
            if perm:
                self.cm.edit_message(message_id, new_message_text)
                socketio.emit(SocketEvents.EDIT_MESSAGE_CLIENT, json.dumps({
                    "message_id": message_id,
                    "new_message_text": new_message_text
                }))

    def handle_message_delete(self, socket_message):
        message_id = socket_message["message_id"]
        op_id = socket_message["op_id"]
        user = User.verify_auth_token(socket_message['token'])
        if user is not None:
            perm = self.permission_check_emit(user.id, int(op_id))
            if perm:
                self.cm.delete_message(message_id)
                socketio.emit(SocketEvents.DELETE_MESSAGE_CLIENT, json.dumps({"message_id": message_id}))

    def permission_check_emit(self, u_id, op_id):
        """
        u_id: user-id
        op_id: operation-id
        """
        permission = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if not permission:
            return False
        if permission.access_level == "viewer":
            return False
        return True

    def permission_check_admin(self, u_id, op_id):
        """
        u_id: user-id
        op_id: operation-id
        """
        permission = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
        if permission.access_level == "creator" or permission.access_level == "admin":
            return True
        else:
            return False

    def handle_file_save(self, json_req):
        """
        json_req: {
            "op_id": operation id
            "content": content of the file
            "comment": comment for file-save, defaults to None
        }
        """

        op_id = json_req['op_id']
        content = json_req['content']
        comment = json_req.get('comment', "")
        version_name = json_req.get('version_name', None)
        messageText = json_req.get('messageText')
        user = User.verify_auth_token(json_req['token'])
        if user is not None:
            # when the socket connection is expired this in None and also on wrong tokens
            perm = self.permission_check_emit(user.id, int(op_id))
            # if permission is correct and file saved properly
            if perm and self.fm.save_file(int(op_id), content, user, version_name=version_name, comment=comment):
                # send service message
                message_ = f"[service message] **{user.username}** saved changes. {messageText}"
                new_message = self.cm.add_message(user, message_, str(op_id), message_type=MessageType.SYSTEM_MESSAGE)
                new_message_dict = get_message_dict(new_message)
                socketio.emit(SocketEvents.CHAT_MESSAGE_CLIENT, json.dumps(new_message_dict))
                # emit file-changed event to trigger reload of flight track
                socketio.emit(SocketEvents.FILE_CHANGED, json.dumps({"op_id": op_id, "u_id": user.id}))
        else:
            logging.debug("Auth Token expired!")

    def emit_file_change(self, op_id):
        socketio.emit(SocketEvents.FILE_CHANGED, json.dumps({"op_id": op_id}))

    def emit_new_permission(self, u_id, op_id):
        """
        to refresh operation list of u_id
        and to refresh collaborators' list
        """
        socketio.emit(SocketEvents.NEW_PERMISSION, json.dumps({"op_id": op_id, "u_id": u_id}))

    def emit_update_permission(self, u_id, op_id, access_level=None):
        """
        to refresh permissions in msui
        """
        if access_level is None:
            perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
            access_level = perm.access_level
            logging.debug("access_level by database query")

        socketio.emit(SocketEvents.UPDATE_PERMISSION, json.dumps({"op_id": op_id, "u_id": u_id,
                                                                  "access_level": access_level}))

    def emit_revoke_permission(self, u_id, op_id):
        socketio.emit(SocketEvents.REVOKE_PERMISSION, json.dumps({"op_id": op_id, "u_id": u_id}))

    def emit_operation_permissions_updated(self, u_id, op_id):
        socketio.emit(SocketEvents.OPERATION_PERMISSIONS_UPDATED, json.dumps({"op_id": op_id, "u_id": u_id}))

    def emit_operation_delete(self, op_id):
        socketio.emit(SocketEvents.OPERATION_DELETED, json.dumps({"op_id": op_id}))


def _setup_managers(app):
    """
    takes app as parameter to extract config data,
    initializes ChatManager, FileManager, SocketManager and return them
    #ToDo return socketio and integrate socketio.cm = ChatManager()
    similarly for FileManager and SocketManager(already done for this)
    """

    cm = ChatManager()
    fm = FileManager(app.config["OPERATIONS_DATA"])
    sm = SocketsManager(cm, fm)
    # sockets related handlers
    socketio.on_event(SocketEvents.CONNECT, sm.handle_connect)
    socketio.on_event(SocketEvents.START, sm.handle_start_event)
    socketio.on_event(SocketEvents.DISCONNECT, sm.handle_disconnect)
    socketio.on_event(SocketEvents.CHAT_MESSAGE, sm.handle_message)
    socketio.on_event(SocketEvents.EDIT_MESSAGE, sm.handle_message_edit)
    socketio.on_event(SocketEvents.DELETE_MESSAGE, sm.handle_message_delete)
    socketio.on_event(SocketEvents.FILE_SAVE, sm.handle_file_save)
    socketio.on_event(SocketEvents.ADD_USER_TO_OPERATION, sm.join_creator_to_operation)
    socketio.on_event(SocketEvents.UPDATE_OPERATION_LIST, sm.update_operation_list)
    # Register the 'operation-selected' event to update active user tracking when an operation is selected
    socketio.on_event(SocketEvents.OPERATION_SELECTED, sm.handle_operation_selected)

    socketio.sm = sm
    return socketio, cm, fm
