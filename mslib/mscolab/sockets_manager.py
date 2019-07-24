# -*- coding: utf-8 -*-
"""

    mslib.mscolab.sockets_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Code to handle socket connections in mscolab

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

from flask_socketio import SocketIO, join_room
from flask import request
import logging
import json

from mslib.mscolab.models import Permission, User
from mslib.mscolab.chat_manager import ChatManager
from mslib.mscolab.file_manager import FileManager

socketio = SocketIO()
cm = ChatManager()
fm = FileManager()


class SocketsManager(object):
    """Class with handler functions for socket related"""

    def __init__(self):
        super(SocketsManager, self).__init__()
        self.sockets = []

    def handle_connect(self):
        logging.debug(request.sid)

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
            cm.add_message(user, _json['message_text'], str(p_id))
            socketio.emit('chat-message-client', json.dumps({'user': user.username,
                                                            'message_text': _json['message_text']}),
                          room=str(p_id))

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
        if perm and fm.save_file(int(p_id), content, user, comment):
            socketio.emit('file-changed', json.dumps({"p_id": p_id, "u_id": user.id}), room=str(p_id))

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
            fm.update_project(int(p_id), 'autosave', 1, user)
            socketio.emit('autosave-client-en', json.dumps({"p_id": p_id}))
        else:
            fm.update_project(int(p_id), 'autosave', 0, user)
            socketio.emit('autosave-client-db', json.dumps({"p_id": p_id}))


sm = SocketsManager()

# sockets related handlers
socketio.on_event('connect', sm.handle_connect)
socketio.on_event('start', sm.handle_start_event)
socketio.on_event('disconnect', sm.handle_disconnect)
socketio.on_event('chat-message', sm.handle_message)
socketio.on_event('file-save', sm.handle_file_save)
socketio.on_event('autosave', sm.handle_autosave_enable)
