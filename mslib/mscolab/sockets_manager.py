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
import re
from flask import request
import flask_socketio
from flask_socketio import SocketIO, join_room

from mslib.mscolab.chat_manager import ChatManager, MAX_MESSAGE_TEXT_LENGTH
from mslib.mscolab.api.events import SocketEvents
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.models import MessageType, Permission, User
from mslib.mscolab.utils import get_message_dict
from mslib.mscolab.utils import get_user_id


def _as_id(value):
    """
    Returns a client-supplied id as int, or None when it is not an int or a string of digits.
    Floats and bools are rejected rather than silently mapped onto another id.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value.strip()):
        return int(value)
    return None


def _valid_message_text(text):
    return isinstance(text, str) and 0 < len(text) <= MAX_MESSAGE_TEXT_LENGTH


class SocketsManager:
    """Class with handler functions for socket related"""

    def __init__(self, chat_manager, file_manager, socketio):
        """
        chat_manager: Instance of ChatManager
        file_manager: Instance of FileManager
        socketio: the Flask-SocketIO instance of the app this manager belongs to
        """
        super(SocketsManager, self).__init__()
        self.sockets = []
        self.active_users_per_operation = {}
        self.cm = chat_manager
        self.fm = file_manager
        self.socketio = socketio

    def handle_connect(self, auth=None):
        """
        auth: {"token": authentication token}, sent by msui on connect

        A connection with an invalid token is refused. One without a token is accepted for older clients,
        it joins no operation room until it sends a valid start event.
        """
        logging.debug(request.sid)
        token = auth.get("token") if isinstance(auth, dict) else None
        if token is None:
            logging.debug("Connection without token, waiting for start event")
            return
        user = User.verify_auth_token(token)
        if user is None:
            raise flask_socketio.ConnectionRefusedError("authentication failed")
        self._join_operation_rooms(user)

    def _bind_socket(self, user):
        """
        Registers the socket of the current request for user, a socket belongs to exactly one user.

        Returns False if the socket is already registered for another user. Otherwise it could join
        rooms with the token of a second user and would not leave them when that user is revoked,
        because emit_revoke_permission only finds the sockets registered for the revoked user.
        """
        u_id = get_user_id(self.sockets, request.sid)
        if u_id is None:
            self.sockets.append({'s_id': request.sid, 'u_id': user.id})
            return True
        if u_id != user.id:
            logging.warning("socket %s of user %s sent a token of user %s, ignored", request.sid, u_id, user.id)
            return False
        return True

    def _join_operation_rooms(self, user):
        """
        Joins the socket of the current request to the rooms of all operations of user and registers it
        """
        if not self._bind_socket(user):
            return
        # a client is always registered as a room with name equal to its session id,
        # so the rooms can safely be named as stringified versions of the operation id
        for permission in Permission.query.filter_by(u_id=user.id).all():
            join_room(self._room(permission.op_id))

    def _user_sids(self, u_id):
        return [d['s_id'] for d in self.sockets if d['u_id'] == u_id]

    @staticmethod
    def _room(op_id):
        """
        Name of the room of operation op_id, normalized so that e.g. "05" and 5 give the same room
        """
        return str(int(op_id))

    def _emit_to_operation(self, event, op_id, *args):
        """
        Emits event only to the sockets in the room of operation op_id, i.e. to its members
        """
        self.socketio.emit(event, *args, to=self._room(op_id))

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
        try:
            op_id = int(json_config['op_id'])
        except (TypeError, ValueError):
            return
        user = User.verify_auth_token(token)
        if user is None or not self.fm.is_member(user.id, op_id):
            return

        # Remove the active user_id from any other operations first
        self.update_active_users(user.id)

        # Add the user to the new operation
        if op_id not in self.active_users_per_operation:
            self.active_users_per_operation[op_id] = set()
        self.active_users_per_operation[op_id].add(user.id)

        # Emit the updated count to all users
        active_count = len(self.active_users_per_operation[op_id])
        self._emit_to_operation(SocketEvents.ACTIVE_USER_UPDATE, op_id, {'op_id': op_id, 'count': active_count})

    def update_operation_list(self, json_config):
        """
        json_config has:
        - token: authentication token
        """
        token = json_config["token"]
        user = User.verify_auth_token(token)
        if user is None:
            return
        self.socketio.emit(SocketEvents.UPDATE_OPERATION_LIST)

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
        if not self.fm.is_member(user.id, op_id) or not self._bind_socket(user):
            return
        join_room(self._room(op_id))

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
        if get_user_id(self.sockets, request.sid) == user.id:
            # msui authenticates on connect already and sends start only for older servers,
            # the rooms are kept up to date by the permission events since then
            return
        self._join_operation_rooms(user)

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
                    self._emit_to_operation(SocketEvents.ACTIVE_USER_UPDATE, op_id,
                                            {'op_id': op_id, 'count': active_count})
                else:
                    # If no users left, delete the operation key
                    del self.active_users_per_operation[op_id]
                    self._emit_to_operation(SocketEvents.ACTIVE_USER_UPDATE, op_id, {'op_id': op_id, 'count': 0})

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
                    self._emit_to_operation(SocketEvents.ACTIVE_USER_UPDATE, op_id,
                                            {'op_id': op_id, 'count': active_count})
                else:
                    # If no users left, delete the operation key
                    del self.active_users_per_operation[op_id]
                    self._emit_to_operation(SocketEvents.ACTIVE_USER_UPDATE, op_id, {'op_id': op_id, 'count': 0})

    def handle_message(self, _json):
        """
        json is a dictionary version of data sent to back-end
        """
        op_id = _as_id(_json.get('op_id'))
        reply_id = _as_id(_json.get("reply_id"))
        message_text = _json.get('message_text')
        if op_id is None or reply_id is None or not _valid_message_text(message_text):
            logging.debug("Invalid chat message rejected")
            return
        user = User.verify_auth_token(_json.get('token'))
        if user is not None:
            perm = self.permission_check_emit(user.id, op_id)
            if perm:
                if reply_id != -1:
                    # a reply belongs to a top-level message of the same operation
                    parent = self.cm.get_message(reply_id, op_id)
                    if parent is None or parent.reply_id is not None:
                        logging.debug("Reply to unknown message %s in operation %s rejected", reply_id, op_id)
                        return
                new_message = self.cm.add_message(user, message_text, str(op_id), reply_id=reply_id)
                self.emit_chat_message(new_message, reply=reply_id != -1)

    def _message_access_level(self, user, message_id, op_id):
        """
        Returns the message `message_id` of operation `op_id` and the access level of `user` on that operation,
        or (None, None) when there is no such message, the user has no permission on the operation or the
        operation is archived, which makes its chat read-only.
        """
        message_id, op_id = _as_id(message_id), _as_id(op_id)
        if message_id is None or op_id is None:
            return None, None
        message = self.cm.get_message(message_id, op_id)
        if message is None:
            return None, None
        access_level = self.fm.auth_type(user.id, op_id)
        if access_level is False or self.fm.is_archived(op_id):
            return None, None
        return message, access_level

    def handle_message_edit(self, socket_message):
        """
        Only the author may edit their own text messages, and only while they may still write to the operation.
        """
        message_id = socket_message.get("message_id")
        op_id = socket_message.get("op_id")
        new_message_text = socket_message.get("new_message_text")
        user = User.verify_auth_token(socket_message.get("token"))
        if user is not None:
            message, access_level = self._message_access_level(user, message_id, op_id)
            if (message is not None and _valid_message_text(new_message_text) and access_level != "viewer" and
                    message.u_id == user.id and message.message_type == MessageType.TEXT):
                self.cm.edit_message(message, new_message_text)
                self._emit_to_operation(SocketEvents.EDIT_MESSAGE_CLIENT, message.op_id, json.dumps({
                    "message_id": message.id,
                    "new_message_text": message.text,
                    "op_id": message.op_id
                }))
            else:
                logging.debug("Edit of message %r in operation %r by %s rejected", message_id, op_id, user.id)

    def handle_message_delete(self, socket_message):
        """
        The author may delete their own messages, except service messages, while they may still write to the
        operation. Deleting a message also deletes its replies, so a message with replies of other users can
        only be deleted by admins and the creator of the operation, who may delete any message of it.
        """
        message_id = socket_message.get("message_id")
        op_id = socket_message.get("op_id")
        user = User.verify_auth_token(socket_message.get('token'))
        if user is not None:
            message, access_level = self._message_access_level(user, message_id, op_id)
            if message is None:
                allowed = False
            elif access_level in ("creator", "admin"):
                allowed = True
            else:
                allowed = (access_level != "viewer" and message.u_id == user.id and
                           message.message_type != MessageType.SYSTEM_MESSAGE and
                           all(reply.u_id == user.id for reply in message.replies))
            if allowed:
                message_id, message_op_id = message.id, message.op_id
                self.cm.delete_message(message)
                self._emit_to_operation(SocketEvents.DELETE_MESSAGE_CLIENT, message_op_id,
                                        json.dumps({"message_id": message_id, "op_id": message_op_id}))
            else:
                logging.debug("Deletion of message %r in operation %r by %s rejected", message_id, op_id, user.id)

    def permission_check_emit(self, u_id, op_id):
        """
        u_id: user-id
        op_id: operation-id

        Whether the user may write to the flight track and the chat of the operation
        """
        return self.fm.may_write(u_id, op_id)

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
            if not self.permission_check_emit(user.id, int(op_id)):
                # e.g. the operation was archived while the user was editing it
                self._refuse_file_save(op_id, "You can't change this operation (any more), e.g. because it "
                                              "was archived or your access level is viewer.")
            elif self.fm.save_file(int(op_id), content, user, version_name=version_name, comment=comment):
                # send service message
                message_ = f"[service message] **{user.username}** saved changes. {messageText}"
                new_message = self.cm.add_message(user, message_, str(op_id), message_type=MessageType.SYSTEM_MESSAGE)
                self.emit_chat_message(new_message)
                # emit file-changed event to trigger reload of flight track
                self._emit_to_operation(SocketEvents.FILE_CHANGED, op_id, json.dumps({"op_id": op_id, "u_id": user.id}))
            else:
                self._refuse_file_save(op_id, "The server could not save the flight track, e.g. because its "
                                              "waypoints or its version name are invalid.")
        else:
            logging.debug("Auth Token expired!")

    def _refuse_file_save(self, op_id, reason):
        """
        Tells the client that sent a FILE_SAVE that its changes were not saved, so it doesn't keep showing them
        """
        self.socketio.emit(SocketEvents.FILE_SAVE_REFUSED, json.dumps({"op_id": op_id, "message": reason}),
                           to=request.sid)

    def emit_chat_message(self, message, reply=False):
        """
        Sends the new chat message to the members of its operation

        The payload names the operation, so msui can drop messages of another operation than the open one.
        """
        event = SocketEvents.CHAT_MESSAGE_REPLY_CLIENT if reply else SocketEvents.CHAT_MESSAGE_CLIENT
        self._emit_to_operation(event, message.op_id, json.dumps(get_message_dict(message) | {"op_id": message.op_id}))

    def emit_file_change(self, op_id):
        self._emit_to_operation(SocketEvents.FILE_CHANGED, op_id, json.dumps({"op_id": op_id}))

    def emit_new_permission(self, u_id, op_id):
        """
        to refresh operation list of u_id
        and to refresh collaborators' list

        The sockets of u_id join the room of the operation first, so they get this and all later events of it.
        """
        for sid in self._user_sids(u_id):
            self.socketio.server.enter_room(sid, self._room(op_id), namespace="/")
        self._emit_to_operation(SocketEvents.NEW_PERMISSION, op_id, json.dumps({"op_id": op_id, "u_id": u_id}))

    def emit_update_permission(self, u_id, op_id, access_level=None):
        """
        to refresh permissions in msui
        """
        if access_level is None:
            perm = Permission.query.filter_by(u_id=u_id, op_id=op_id).first()
            access_level = perm.access_level
            logging.debug("access_level by database query")

        self._emit_to_operation(SocketEvents.UPDATE_PERMISSION, op_id,
                                json.dumps({"op_id": op_id, "u_id": u_id, "access_level": access_level}))

    def emit_revoke_permission(self, u_id, op_id):
        """
        The sockets of u_id still get this event, then they leave the room of the operation
        """
        self._emit_to_operation(SocketEvents.REVOKE_PERMISSION, op_id, json.dumps({"op_id": op_id, "u_id": u_id}))
        for sid in self._user_sids(u_id):
            self.socketio.server.leave_room(sid, self._room(op_id), namespace="/")

    def forget_user(self, u_id):
        """
        For a deleted account: its sockets leave all operation rooms and are no longer registered for u_id

        Otherwise a later user who gets the same id, e.g. on SQLite, would put these sockets into their rooms.
        The sockets stay connected like a socket without a token.
        """
        self.update_active_users(u_id)
        for sid in self._user_sids(u_id):
            for room in list(self.socketio.server.rooms(sid, namespace="/")):
                # the room named by its own sid is not an operation room
                if room.isdigit():
                    self.socketio.server.leave_room(sid, room, namespace="/")
        self.sockets[:] = [d for d in self.sockets if d['u_id'] != u_id]

    def sync_rooms(self):
        """
        Makes the rooms of every registered socket match the operations its user is a member of

        For changes of many permissions at once, e.g. the import of the permissions of a group
        operation, where the added and removed users are not known to the caller.
        """
        members = {}
        for permission in Permission.query.all():
            members.setdefault(permission.u_id, set()).add(self._room(permission.op_id))
        for d in self.sockets:
            wanted = members.get(d['u_id'], set())
            # the room named by its own sid is not an operation room
            joined = {room for room in self.socketio.server.rooms(d['s_id'], namespace="/") if room.isdigit()}
            for room in wanted - joined:
                self.socketio.server.enter_room(d['s_id'], room, namespace="/")
            for room in joined - wanted:
                self.socketio.server.leave_room(d['s_id'], room, namespace="/")

    def emit_operation_permissions_updated(self, u_id, op_id):
        self._emit_to_operation(SocketEvents.OPERATION_PERMISSIONS_UPDATED, op_id,
                                json.dumps({"op_id": op_id, "u_id": u_id}))

    def emit_operation_delete(self, op_id):
        self._emit_to_operation(SocketEvents.OPERATION_DELETED, op_id, json.dumps({"op_id": op_id}))
        self.socketio.server.close_room(self._room(op_id), namespace="/")

    def emit_operation_list_update(self):
        """
        Broadcasts that operation lists may be stale, e.g. after an operation was
        archived. Unlike update_operation_list, this doesn't require a client token
        since it's also called from the internal admin notify endpoint on behalf of
        the CLI, which has no client session.
        """
        self.socketio.emit(SocketEvents.UPDATE_OPERATION_LIST)


def _setup_managers(app):
    """
    takes app as parameter to extract config data,
    initializes ChatManager, FileManager, SocketManager and return them
    #ToDo return socketio and integrate socketio.cm = ChatManager()
    similarly for FileManager and SocketManager(already done for this)

    A new SocketIO instance is created for every app, so that two apps existing at the
    same time (e.g. in the tests) cannot overwrite each other's event handlers. It is
    bound to the app by SocketIO.init_app, which is also where the options depending on
    the app configuration are passed, see mslib.mscolab.server._initialize_managers.
    """
    # async_handlers=False handles each client's events in the order they were received.
    # With the default (async_handlers=True) every event runs in its own thread, so two
    # rapid file-save events can give a wrong final document data.
    socketio = SocketIO(async_mode='threading', async_handlers=False)

    cm = ChatManager()
    fm = FileManager(app.config["OPERATIONS_DATA"])
    sm = SocketsManager(cm, fm, socketio)
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
