# -*- coding: utf-8 -*-
"""

    mslib.mscolab.sockets_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
from flask_socketio import SocketIO, join_room, leave_room

from mslib.mscolab.chat_manager import ChatManager
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.models import MessageType, Permission, User
from mslib.mscolab.utils import get_message_dict
from mslib.mscolab.utils import get_session_id

socketio = SocketIO()


class SocketsManager(object):
    """Class with handler functions for socket related"""

    def __init__(self, chat_manager, file_manager):
        """
        chat_manager: Instance of ChatManager
        file_manager: Instance of FileManager
        """
        super(SocketsManager, self).__init__()
        self.sockets = []
        self.cm = chat_manager
        self.fm = file_manager

    def handle_connect(self):
        logging.debug(request.sid)

    def join_creator_to_room(self, json):
        """
        json has:
            - token: authentication token
            - p_id: project id
        """
        token = json['token']
        user = User.verify_auth_token(token)
        if not user:
            return
        p_id = json['p_id']
        join_room(str(p_id))

    def join_collaborator_to_room(self, u_id, p_id):
        """
        json has:
            - u_id: user id(collaborator's id)
            - p_id: project id
        """
        s_id = get_session_id(self.sockets, u_id)
        if s_id is not None:
            join_room(str(p_id), sid=s_id, namespace='/')

    def remove_collaborator_from_room(self, u_id, p_id):
        s_id = get_session_id(self.sockets, u_id)
        if s_id is not None:
            leave_room(str(p_id), sid=s_id, namespace='/')

    def handle_start_event(self, json):
        """
        json is a dictionary version of data sent to backend
        """
        logging.info('received json: ' + str(json))
        # authenticate socket
        token = json['token']
        user = User.verify_auth_token(token)
        if not user:
            return

        # fetch projects
        permissions = Permission.query.filter_by(u_id=user.id).all()

        # for all the p_id in permissions, there'd be chatrooms in self.rooms
        # search and add user to respective rooms
        for permission in permissions:
            # for each project with p_id, search rooms
            # socketio.join_room(room, sid=None, namespace=None)
            """
            - a client is always registered as a room with name equal to
            the session id of the client.
            - so the rooms can safely be named as stringified versions of
            the project id.
            - thus, an abstraction is unnecessary. if it will be, it'll be
            considered during later developments.
            - so joining the actual socketio room would be enough
            """
            join_room(str(permission.p_id))
        socket_storage = {
            's_id': request.sid,
            'u_id': user.id
        }
        self.sockets.append(socket_storage)

    def handle_disconnect(self):
        logging.info("disconnected")
        logging.info(request.sid)
        # remove socket from socket_storage
        self.sockets[:] = [d for d in self.sockets if d['s_id'] != request.sid]

    def handle_message(self, _json):
        """
        json is a dictionary version of data sent to back-end
        """
        p_id = _json['p_id']
        user = User.verify_auth_token(_json['token'])
        perm = self.permission_check_emit(user.id, int(p_id))
        if perm:
            new_message = self.cm.add_message(user, _json['message_text'], str(p_id))
            new_message_dict = get_message_dict(new_message, user)
            socketio.emit('chat-message-client', json.dumps(new_message_dict), room=str(p_id))

    def handle_message_edit(self, socket_message):
        message_id = socket_message["message_id"]
        p_id = socket_message["p_id"]
        new_message_text = socket_message["new_message_text"]
        user = User.verify_auth_token(socket_message["token"])
        perm = self.permission_check_emit(user.id, int(p_id))
        if perm:
            self.cm.edit_message(message_id, new_message_text)
            socketio.emit('edit-message-client', json.dumps({
                "message_id": message_id,
                "new_message_text": new_message_text
            }), room=str(p_id))

    def handle_message_delete(self, socket_message):
        message_id = socket_message["message_id"]
        p_id = socket_message["p_id"]
        user = User.verify_auth_token(socket_message['token'])
        perm = self.permission_check_emit(user.id, int(p_id))
        if perm:
            self.cm.delete_message(message_id)
            socketio.emit('delete-message-client', json.dumps({"message_id": message_id}), room=str(p_id))

    def permission_check_emit(self, u_id, p_id):
        """
        u_id: user-id
        p_id: project-id
        """
        permission = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if not permission:
            return False
        if permission.access_level == "viewer":
            return False
        return True

    def permission_check_admin(self, u_id, p_id):
        """
        u_id: user-id
        p_id: project-id
        """
        permission = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        if permission.access_level == "creator" or permission.access_level == "admin":
            return True
        else:
            return False

    def handle_file_save(self, json_req):
        """
        json_req: {
            "p_id": process id
            "content": content of the file
            "comment": comment for file-save, defaults to None
        }
        """

        p_id = json_req['p_id']
        content = json_req['content']
        comment = json_req.get('comment', "")
        user = User.verify_auth_token(json_req['token'])
        perm = self.permission_check_emit(user.id, int(p_id))
        # if permission is correct and file saved properly
        if perm and self.fm.save_file(int(p_id), content, user, comment):
            # send service message
            message_ = "[service message] saved changes"
            new_message = self.cm.add_message(user, message_, str(p_id), message_type=MessageType.SYSTEM_MESSAGE)
            new_message_dict = get_message_dict(new_message, user)
            socketio.emit('chat-message-client', json.dumps(new_message_dict), room=str(p_id))
            # emit file-changed event to trigger reload of flight track
            socketio.emit('file-changed', json.dumps({"p_id": p_id, "u_id": user.id}), room=str(p_id))

    def emit_file_change(self, p_id):
        socketio.emit('file-changed', json.dumps({"p_id": p_id}), room=str(p_id))

    def handle_autosave_enable(self, json_req):
        """
        json_req: {
            "p_id": process id
            "enable": boolean to enable or disable autosave
        }
        """
        p_id = json_req['p_id']
        enable = json_req['enable']
        user = User.verify_auth_token(json_req['token'])
        # save to project database
        if not self.permission_check_admin(user.id, p_id):
            return
        if enable:
            self.fm.update_project(int(p_id), 'autosave', 1, user)
            socketio.emit('autosave-client-en', json.dumps({"p_id": p_id}))
        else:
            self.fm.update_project(int(p_id), 'autosave', 0, user)
            socketio.emit('autosave-client-db', json.dumps({"p_id": p_id}))

    def emit_new_permission(self, u_id, p_id):
        """
        to refresh project list of u_id
        and to refresh collaborators' list
        """
        socketio.emit('new-permission', json.dumps({"p_id": p_id, "u_id": u_id}), room=str(p_id))

    def emit_update_permission(self, u_id, p_id):
        """
        to refresh permissions in msui
        """
        perm = Permission.query.filter_by(u_id=u_id, p_id=p_id).first()
        socketio.emit('update-permission', json.dumps({"p_id": p_id,
                                                       "u_id": u_id,
                                                       "access_level": perm.access_level}), room=str(p_id))

    def emit_revoke_permission(self, u_id, p_id):
        socketio.emit("revoke-permission", json.dumps({"p_id": p_id, "u_id": u_id}), room=str(p_id))

    def emit_project_permissions_updated(self, u_id, p_id):
        socketio.emit("project-permissions-updated", json.dumps({"u_id": u_id}), room=str(p_id))


def setup_managers(app):
    """
    takes app as parameter to extract config data,
    initializes ChatManager, FileManager, SocketManager and return them
    #ToDo return socketio and integrate socketio.cm = ChatManager()
    similarly for FileManager and SocketManager(already done for this)
    """

    cm = ChatManager()
    fm = FileManager(app.config["MSCOLAB_DATA_DIR"])
    sm = SocketsManager(cm, fm)
    # sockets related handlers
    socketio.on_event('connect', sm.handle_connect)
    socketio.on_event('start', sm.handle_start_event)
    socketio.on_event('disconnect', sm.handle_disconnect)
    socketio.on_event('chat-message', sm.handle_message)
    socketio.on_event('edit-message', sm.handle_message_edit)
    socketio.on_event('delete-message', sm.handle_message_delete)
    socketio.on_event('file-save', sm.handle_file_save)
    socketio.on_event('autosave', sm.handle_autosave_enable)
    socketio.on_event('add-user-to-room', sm.join_creator_to_room)
    socketio.sm = sm
    return socketio, cm, fm
