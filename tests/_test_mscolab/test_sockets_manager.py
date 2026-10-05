# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_sockets
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for sockets module

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
import os
import json
import pytest
import datetime

from mslib.msui.icons import icons
from mslib.mscolab.api.events import SocketEvents
from mslib.mscolab.chat_manager import MAX_MESSAGE_TEXT_LENGTH
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation, get_operation, \
    XML_CONTENT_INIT
from mslib.mscolab.models import db, Change, Operation, Permission, User, Message, MessageType
from tests.utils import XML_CONTENT1


class Test_Socket_Manager:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        self.sockio, self.cm, self.fm = mscolab_managers
        self.sm = self.sockio.sm
        self.sockets = []
        self.userdata = 'UV10@uv10', 'UV10', 'uv10', 'User UV'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20', 'User UVs'
        self.operation_name = "europe"
        with self.app.app_context():
            assert add_user(self.userdata[0], self.userdata[1], self.userdata[2], self.userdata[3])
            assert add_operation(self.operation_name, "test europe")
            assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
            self.user = get_user(self.userdata[0])
            assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2],
                            self.anotheruserdata[3])
            self.anotheruser = get_user(self.anotheruserdata[0])
            self.token = self.user.generate_auth_token()
            self.operation = get_operation(self.operation_name)
        yield
        for sock in self.sockets:
            sock.disconnect()

    def _connect(self, token=None):
        """
        token: sent on connect like msui does, the socket joins the rooms of the operations of its user.
        Without one it connects like an older client, which joins rooms only with the start event.
        """
        sio = self.sockio.test_client(self.app, auth={"token": token} if token is not None else None)
        self.sockets.append(sio)
        sio.emit('connect')
        return sio

    def _another_token(self):
        with self.app.app_context():
            return self.anotheruser.generate_auth_token()

    def _send(self, sio, text, op_id=None):
        sio.emit("chat-message", {"op_id": op_id or self.operation.id, "token": self.token,
                                  "message_text": text, "reply_id": -1})

    @staticmethod
    def _events(sio, name=None):
        return [r for r in sio.get_received() if name is None or r["name"] == name]

    def _new_operation(self, operation_name, description):
        with self.app.app_context():
            assert add_operation(operation_name, description)
            operation = get_operation(operation_name)
        return operation

    def test_handle_connect(self):
        sio = self._connect()
        assert len(sio.eio_sid) > 5

    def test_join_creator_to_operatiom(self):
        sio = self._connect()
        operation = self._new_operation('new_operation', "example description")
        with self.app.app_context():
            assert self.fm.get_file(int(operation.id), self.user) is False
        json_config = {"token": self.token,
                       "op_id": operation.id}

        sio.emit('add-user-to-operation', json_config)
        perms = Permission(self.user.id, operation.id, "creator")
        assert perms.op_id == operation.id
        assert perms.u_id == self.user.id
        assert perms.access_level == "creator"

    def test_active_user_tracking_and_emissions_on_operation_selection(self):
        """
        Test that selecting an operation tracks the active user count appropriately
        and verifies that the correct events are emitted.
        """
        sio = self._connect(self.token)

        # Initial state: no active users for the operation
        assert self.operation.id not in self.sm.active_users_per_operation

        # User selects an operation
        sio.emit("operation-selected", {"token": self.token, "op_id": self.operation.id})

        # Check internal server tracking
        assert self.operation.id in self.sm.active_users_per_operation
        assert self.user.id in self.sm.active_users_per_operation[self.operation.id]
        assert len(self.sm.active_users_per_operation[self.operation.id]) == 1

        # Verify that the correct event is emitted
        received_messages = sio.get_received()
        assert len(received_messages) == 1
        received_message_args = received_messages[0]["args"][0]
        assert received_message_args["op_id"] == self.operation.id
        assert received_message_args["count"] == 1

        # Testing with multiple users
        with self.app.app_context():
            add_user_to_operation(path=self.operation_name, emailid=self.anotheruserdata[0])
            another_token = self.anotheruser.generate_auth_token()
        another_sio = self._connect(another_token)
        another_sio.emit("operation-selected",
                         {"token": another_token, "op_id": self.operation.id})

        # Check internal server tracking
        assert self.anotheruser.id in self.sm.active_users_per_operation[self.operation.id]
        assert len(self.sm.active_users_per_operation[self.operation.id]) == 2

        # Verify that the active user count is updated for both clients
        updated_messages = another_sio.get_received()
        assert len(updated_messages) == 1
        updated_message_args = updated_messages[0]["args"][0]
        assert updated_message_args["op_id"] == self.operation.id
        assert updated_message_args["count"] == 2

    def test_connect_with_invalid_token_is_refused(self):
        sio = self.sockio.test_client(self.app, auth={"token": "invalid"})
        assert not sio.is_connected()

    def test_chat_events_only_reach_members(self):
        # H1: the events of an operation go to the room of the operation, not to every socket
        member = self._connect(self.token)
        outsider = self._connect(self._another_token())
        anonymous = self._connect()
        self._send(member, "only for members")
        with self.app.app_context():
            message = Message.query.filter_by(text="only for members").first()
        member.emit("edit-message", {"message_id": message.id, "new_message_text": "edited",
                                     "op_id": self.operation.id, "token": self.token})
        member.emit("delete-message", {"message_id": message.id, "op_id": self.operation.id,
                                       "token": self.token})

        received = {r["name"]: json.loads(r["args"][0]) for r in self._events(member)}
        # the payloads name the operation, so msui can drop events of another operation than the open one
        assert received[SocketEvents.CHAT_MESSAGE_CLIENT]["op_id"] == self.operation.id
        assert received[SocketEvents.CHAT_MESSAGE_CLIENT]["text"] == "only for members"
        assert received[SocketEvents.EDIT_MESSAGE_CLIENT] == {
            "message_id": message.id, "new_message_text": "edited", "op_id": self.operation.id}
        assert received[SocketEvents.DELETE_MESSAGE_CLIENT] == {
            "message_id": message.id, "op_id": self.operation.id}
        assert self._events(outsider) == []
        assert self._events(anonymous) == []

    def test_start_event_joins_rooms(self):
        # an older client connects without a token and authenticates with the start event
        sio = self._connect()
        sio.emit('start', {'token': self.token})
        self._send(sio, "after start")
        assert len(self._events(sio, SocketEvents.CHAT_MESSAGE_CLIENT)) == 1

    def test_start_event_after_authenticated_connect_joins_no_room_again(self, monkeypatch):
        # msui authenticates on connect and sends start as well, the rooms are joined only once
        joins = []
        join_operation_rooms = self.sm._join_operation_rooms
        monkeypatch.setattr(self.sm, "_join_operation_rooms", lambda user: joins.append(user.id) or
                            join_operation_rooms(user))
        sio = self._connect(self.token)
        sio.emit('start', {'token': self.token})
        assert joins == [self.user.id]
        self._send(sio, "joined once")
        assert len(self._events(sio, SocketEvents.CHAT_MESSAGE_CLIENT)) == 1

    def test_start_event_with_invalid_token_joins_no_room(self):
        sio = self._connect()
        sio.emit('start', {'token': "invalid"})
        member = self._connect(self.token)
        self._send(member, "not for invalid tokens")
        assert self._events(sio) == []

    def test_join_operation_room_requires_membership(self):
        # M8: add-user-to-operation and operation-selected only work for members of the operation
        another_token = self._another_token()
        outsider = self._connect(another_token)
        outsider.emit("add-user-to-operation", {"token": another_token, "op_id": self.operation.id})
        outsider.emit("operation-selected", {"token": another_token, "op_id": self.operation.id})
        assert self.operation.id not in self.sm.active_users_per_operation
        member = self._connect(self.token)
        self._send(member, "not for outsiders")
        assert self._events(outsider) == []

    def test_new_permission_joins_and_revoke_leaves_room(self):
        outsider = self._connect(self._another_token())
        member = self._connect(self.token)
        with self.app.app_context():
            assert add_user_to_operation(path=self.operation_name, emailid=self.anotheruserdata[0])
        self.sm.emit_new_permission(self.anotheruser.id, self.operation.id)
        assert len(self._events(outsider, SocketEvents.NEW_PERMISSION)) == 1
        self._send(member, "for the new member")
        assert len(self._events(outsider, SocketEvents.CHAT_MESSAGE_CLIENT)) == 1

        with self.app.app_context():
            Permission.query.filter_by(u_id=self.anotheruser.id, op_id=self.operation.id).delete()
            db.session.commit()
        self.sm.emit_revoke_permission(self.anotheruser.id, self.operation.id)
        # the removed user is still told, then leaves the room
        assert len(self._events(outsider, SocketEvents.REVOKE_PERMISSION)) == 1
        self._send(member, "no longer for the removed member")
        assert self._events(outsider) == []

    def test_operation_delete_closes_room(self):
        member = self._connect(self.token)
        self.sm.emit_operation_delete(self.operation.id)
        assert len(self._events(member, SocketEvents.OPERATION_DELETED)) == 1
        self.sm.emit_file_change(self.operation.id)
        assert self._events(member) == []

    def test_socket_ignores_token_of_another_user(self):
        # a socket belongs to the user it authenticated with first, with the token of a second user
        # it would join rooms from which it is not removed when that second user is revoked
        outsider = self._connect(self._another_token())
        outsider.emit('start', {'token': self.token})
        outsider.emit("add-user-to-operation", {"token": self.token, "op_id": self.operation.id})
        member = self._connect(self.token)
        self._send(member, "not for another socket")
        assert self._events(outsider) == []

    def test_sync_rooms_follows_permissions(self):
        outsider = self._connect(self._another_token())
        member = self._connect(self.token)
        with self.app.app_context():
            db.session.add(Permission(self.anotheruser.id, self.operation.id, "collaborator"))
            db.session.commit()
            self.sm.sync_rooms()
        self._send(member, "after the permission was added")
        assert len(self._events(outsider, SocketEvents.CHAT_MESSAGE_CLIENT)) == 1
        with self.app.app_context():
            Permission.query.filter_by(u_id=self.anotheruser.id, op_id=self.operation.id).delete()
            db.session.commit()
            self.sm.sync_rooms()
        self._send(member, "after the permission was removed")
        assert self._events(outsider) == []

    def _group_operation(self, category, member):
        """
        Creates the group operation of category, the permissions of its members are imported into
        the other operations of the category
        """
        path = f"{category}{self.app.config['GROUP_POSTFIX']}"
        with self.app.app_context():
            assert add_operation(path, "group")
            assert add_user_to_operation(path=path, access_level="creator", emailid=self.userdata[0])
            if member is not None:
                assert add_user_to_operation(path=path, access_level="collaborator", emailid=member)
            return get_operation(path)

    def test_create_operation_in_group_category_joins_rooms(self):
        self._group_operation("syncgroup", self.anotheruserdata[0])
        outsider = self._connect(self._another_token())
        response = self.app.test_client().post("/create_operation", data={
            "token": self.token, "path": "syncgroupop", "description": "in a group", "category": "syncgroup",
            "content": XML_CONTENT_INIT})
        assert response.data.decode() == "True"
        with self.app.app_context():
            op_id = get_operation("syncgroupop").id
        outsider.get_received()
        self.sm.emit_file_change(op_id)
        assert len(self._events(outsider, SocketEvents.FILE_CHANGED)) == 1

    def test_bulk_permission_on_group_operation_joins_rooms(self):
        group = self._group_operation("bulkgroup", None)
        with self.app.app_context():
            assert self.fm.create_operation("bulkgroupop", "in a group", self.user, category="bulkgroup",
                                            content=XML_CONTENT_INIT)
            op_id = get_operation("bulkgroupop").id
            assert add_user('UV30@uv30', 'UV30', 'uv30', 'User UV3')
            thirduser = get_user('UV30@uv30')
            third_token = thirduser.generate_auth_token()
        outsiders = [self._connect(self._another_token()), self._connect(third_token)]
        response = self.app.test_client().post("/add_bulk_permissions", data={
            "token": self.token, "op_id": group.id, "selected_access_level": "collaborator",
            "selected_userids": json.dumps([self.anotheruser.id, thirduser.id])})
        assert response.json["success"] is True
        for outsider in outsiders:
            outsider.get_received()
        self.sm.emit_file_change(op_id)
        # all users are added to the operations of the category, not only the last one
        for outsider in outsiders:
            assert len(self._events(outsider, SocketEvents.FILE_CHANGED)) == 1

    def test_rename_to_group_operation_joins_rooms(self):
        with self.app.app_context():
            assert self.fm.create_operation("renamegroupop", "in a group", self.user, category="renamegroup",
                                            content=XML_CONTENT_INIT)
            op_id = get_operation("renamegroupop").id
            assert add_user_to_operation(path=self.operation_name, access_level="collaborator",
                                         emailid=self.anotheruserdata[0])
        outsider = self._connect(self._another_token())
        response = self.app.test_client().post("/update_operation", data={
            "token": self.token, "op_id": self.operation.id, "attribute": "path",
            "value": f"renamegroup{self.app.config['GROUP_POSTFIX']}"})
        assert response.data.decode() == "True"
        outsider.get_received()
        self.sm.emit_file_change(op_id)
        assert len(self._events(outsider, SocketEvents.FILE_CHANGED)) == 1

    def test_delete_own_account_leaves_rooms(self):
        with self.app.app_context():
            assert add_user_to_operation(path=self.operation_name, emailid=self.anotheruserdata[0])
        removed = self._connect(self._another_token())
        member = self._connect(self.token)
        response = self.app.test_client().post("/delete_own_account", data={"token": self._another_token()})
        assert response.json["success"] is True
        assert len(self._events(removed, SocketEvents.REVOKE_PERMISSION)) == 1
        self._send(member, "not for deleted users")
        assert self._events(removed) == []

    def test_delete_own_account_unregisters_sockets(self):
        with self.app.app_context():
            assert add_user_to_operation(path=self.operation_name, emailid=self.anotheruserdata[0])
            u_id = self.anotheruser.id
        removed = self._connect(self._another_token())
        removed.emit("operation-selected", {"token": self._another_token(), "op_id": self.operation.id})
        member = self._connect(self.token)
        assert u_id in self.sm.active_users_per_operation[self.operation.id]
        response = self.app.test_client().post("/delete_own_account", data={"token": self._another_token()})
        assert response.json["success"] is True
        assert u_id not in self.sm.active_users_per_operation.get(self.operation.id, set())
        assert [d for d in self.sm.sockets if d["u_id"] == u_id] == []
        removed.get_received()
        # a new account can get the same id on SQLite, its permissions must not reach the old sockets
        self.sm.emit_new_permission(u_id, self.operation.id)
        self._send(member, "not for the old sockets")
        assert self._events(removed) == []

    def test_room_name_is_normalized(self):
        member = self._connect(self.token)
        self._send(member, "normalized", op_id=f"0{self.operation.id}")
        received = self._events(member, SocketEvents.CHAT_MESSAGE_CLIENT)
        assert len(received) == 1
        assert json.loads(received[0]["args"][0])["op_id"] == self.operation.id

    @pytest.mark.skip(reason="unknown how to verify")
    def test_handle_start_event(self):
        sio = self._connect()
        json_config = {"token": self.token}
        assert User.verify_auth_token(self.token) is not False
        sio.emit('start', json_config)

    def test_send_message(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "op_id": self.operation.id,
            "token": self.token,
            "message_text": "message from 1",
            "reply_id": -1
        })

        # testing non-ascii message
        sio.emit("chat-message", {
            "op_id": self.operation.id,
            "token": self.token,
            "message_text": "® non ascii",
            "reply_id": -1
        })

        with self.app.app_context():
            message = Message.query.filter_by(text="message from 1").first()
            assert message.op_id == self.operation.id
            assert message.u_id == self.user.id

            message = Message.query.filter_by(text="® non ascii").first()
            assert message is not None

    def test_get_messages(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        for _ in range(2):
            sio.emit("chat-message", {
                "op_id": self.operation.id,
                "token": self.token,
                "message_text": "message from 1",
                "reply_id": -1
            })

        with self.app.app_context():
            messages = self.cm.get_messages(1)
            assert messages[0]["text"] == "message from 1"
            assert len(messages) == 2
            assert messages[0]["u_id"] == self.user.id
            timestamp = datetime.datetime(1970, 1, 1,
                                          tzinfo=datetime.timezone.utc).isoformat()
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 2
            assert messages[0]["u_id"] == self.user.id
            timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            messages = self.cm.get_messages(1, timestamp)
            assert len(messages) == 0

    def test_get_messages_api(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})
        for _ in range(2):
            sio.emit("chat-message", {
                "op_id": self.operation.id,
                "token": self.token,
                "message_text": "message from 1",
                "reply_id": -1
            })

        token = self.token
        data = {
            "token": token,
            "op_id": self.operation.id,
            "timestamp": datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
        }
        with self.app.test_client() as c:
            res = c.get("/messages", data=data)
            assert len(res.json["messages"]) == 2

            data["token"] = "dummy"
            # returns False due to bad authorization
            r = c.get("/messages", data=data)
            assert r.text == "False"

    def test_edit_message(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "op_id": self.operation.id,
            "token": self.token,
            "message_text": "Edit this message",
            "reply_id": -1
        })
        with self.app.app_context():
            message = Message.query.filter_by(text="Edit this message").first()
        sio.emit('edit-message', {
            "message_id": message.id,
            "new_message_text": "I have updated the message",
            "op_id": message.op_id,
            "token": self.token
        })
        token = self.token
        data = {
            "token": token,
            "op_id": self.operation.id,
            "timestamp": datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
        }
        with self.app.test_client() as c:
            res = c.get("messages", data=data).json
        assert len(res["messages"]) == 1
        messages = res["messages"][0]
        assert messages["text"] == "I have updated the message"

    def test_delete_message(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})

        sio.emit("chat-message", {
            "op_id": self.operation.id,
            "token": self.token,
            "message_text": "delete this message",
            "reply_id": -1
        })

        with self.app.app_context():
            message = Message.query.filter_by(text="delete this message").first()
        sio.emit('delete-message', {
            'message_id': message.id,
            'op_id': self.operation.id,
            'token': self.token
        })

        with self.app.app_context():
            assert Message.query.filter_by(text="delete this message").count() == 0

    def test_upload_file(self):
        sio = self._connect()
        sio.emit('start', {'token': self.token})
        data = {
            "token": self.token,
            "op_id": self.operation.id,
            "message_type": int(MessageType.IMAGE),
            "file": open(icons('16x16'), 'rb'),
        }
        with self.app.test_client() as c:
            c.post("message_attachment", data=data, content_type="multipart/form-data")
        upload_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], str(self.user.id))
        assert os.path.exists(upload_dir)
        file = os.listdir(upload_dir)[0]
        assert 'mss-logo' in file
        assert 'png' in file
        # the members of the operation get the attachment as chat message
        received = self._events(sio, SocketEvents.CHAT_MESSAGE_CLIENT)
        assert len(received) == 1
        message = json.loads(received[0]["args"][0])
        assert message["op_id"] == self.operation.id
        assert message["message_type"] == int(MessageType.IMAGE)

    def _add_message(self, user, operation, text, message_type=MessageType.TEXT, reply_id=None):
        with self.app.app_context():
            message = self.cm.add_message(user, text, operation.id, message_type=message_type, reply_id=reply_id)
            return message.id

    def _message_text(self, message_id):
        with self.app.app_context():
            message = Message.query.filter_by(id=message_id).first()
            return None if message is None else message.text

    def _add_user_to_operation(self, userdata, operation_name, access_level):
        with self.app.app_context():
            assert add_user_to_operation(path=operation_name, emailid=userdata[0], access_level=access_level)
            return get_user(userdata[0]).generate_auth_token()

    def test_edit_and_delete_message_of_other_operation_rejected(self):
        # the attacker is creator of an operation of their own and names it in the request
        attacker_operation_id = self._new_operation("attacker", "attacker operation").id
        attacker_token = self._add_user_to_operation(self.anotheruserdata, "attacker", "creator")
        message_id = self._add_message(self.user, self.operation, "victim message")
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": "rewritten",
            "op_id": attacker_operation_id,
            "token": attacker_token
        })
        sio.emit('delete-message', {
            "message_id": message_id,
            "op_id": attacker_operation_id,
            "token": attacker_token
        })
        assert self._message_text(message_id) == "victim message"
        assert self._events(sio, 'edit-message-client') == []
        assert self._events(sio, 'delete-message-client') == []

    def test_edit_message_only_by_author(self):
        # another admin of the same operation can not edit the message
        another_token = self._add_user_to_operation(self.anotheruserdata, self.operation_name, "admin")
        message_id = self._add_message(self.user, self.operation, "author message")
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": "rewritten",
            "op_id": self.operation.id,
            "token": another_token
        })
        assert self._message_text(message_id) == "author message"
        assert self._events(sio, 'edit-message-client') == []

    @pytest.mark.parametrize("message_type", [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.SYSTEM_MESSAGE])
    def test_edit_message_only_text(self, message_type):
        message_id = self._add_message(self.user, self.operation, "uploads/1/file.png", message_type=message_type)
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": "https://attacker.example/x",
            "op_id": self.operation.id,
            "token": self.token
        })
        assert self._message_text(message_id) == "uploads/1/file.png"
        assert self._events(sio, 'edit-message-client') == []

    def test_viewer_can_not_edit_or_delete_own_message(self):
        message_id = self._add_message(self.anotheruser, self.operation, "written before downgrade")
        viewer_token = self._add_user_to_operation(self.anotheruserdata, self.operation_name, "viewer")
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": "rewritten",
            "op_id": self.operation.id,
            "token": viewer_token
        })
        sio.emit('delete-message', {
            "message_id": message_id,
            "op_id": self.operation.id,
            "token": viewer_token
        })
        assert self._message_text(message_id) == "written before downgrade"
        assert self._events(sio, 'edit-message-client') == []
        assert self._events(sio, 'delete-message-client') == []

    def test_collaborator_deletes_only_own_messages(self):
        collaborator_token = self._add_user_to_operation(self.anotheruserdata, self.operation_name, "collaborator")
        own_id = self._add_message(self.anotheruser, self.operation, "own message")
        other_id = self._add_message(self.user, self.operation, "other message")
        system_id = self._add_message(self.anotheruser, self.operation, "[service message] saved",
                                      message_type=MessageType.SYSTEM_MESSAGE)
        sio = self._connect(self.token)
        for message_id in (own_id, other_id, system_id):
            sio.emit('delete-message', {
                "message_id": message_id,
                "op_id": self.operation.id,
                "token": collaborator_token
            })
        assert self._message_text(own_id) is None
        assert self._message_text(other_id) == "other message"
        assert self._message_text(system_id) == "[service message] saved"
        assert [json.loads(msg["args"][0])["message_id"] for msg in self._events(sio, 'delete-message-client')] \
            == [own_id]

    @pytest.mark.parametrize("access_level", ["admin", "creator"])
    def test_admin_and_creator_delete_any_message_of_operation(self, access_level):
        token = self._add_user_to_operation(self.anotheruserdata, self.operation_name, access_level)
        text_id = self._add_message(self.user, self.operation, "other message")
        system_id = self._add_message(self.user, self.operation, "[service message] saved",
                                      message_type=MessageType.SYSTEM_MESSAGE)
        sio = self._connect(self.token)
        for message_id in (text_id, system_id):
            sio.emit('delete-message', {
                "message_id": message_id,
                "op_id": self.operation.id,
                "token": token
            })
        assert self._message_text(text_id) is None
        assert self._message_text(system_id) is None
        assert len(self._events(sio, 'delete-message-client')) == 2

    @pytest.mark.parametrize("message_id", [987654, "no-id", None, 1.5, True, "missing"])
    def test_edit_and_delete_unknown_message(self, message_id):
        # a float or bool id must not be mapped onto another message
        self._add_message(self.user, self.operation, "first message")
        sio = self._connect(self.token)
        edit = {"new_message_text": "rewritten", "op_id": self.operation.id, "token": self.token}
        delete = {"op_id": self.operation.id, "token": self.token}
        if message_id != "missing":
            edit["message_id"] = delete["message_id"] = message_id
        sio.emit('edit-message', edit)
        sio.emit('delete-message', delete)
        assert self._events(sio, 'edit-message-client') == []
        assert self._events(sio, 'delete-message-client') == []
        with self.app.app_context():
            assert Message.query.filter_by(text="first message").count() == 1

    @pytest.mark.parametrize("payload", [{}, {"token": "dummy"}, {"message_id": 1}, {"op_id": 1}])
    def test_edit_and_delete_missing_keys(self, payload):
        sio = self._connect(self.token)
        sio.emit('edit-message', payload)
        sio.emit('delete-message', payload)
        sio.emit('chat-message', payload)
        assert sio.get_received() == []

    @pytest.mark.parametrize("new_message_text", [None, {}, 42, "", "x" * (MAX_MESSAGE_TEXT_LENGTH + 1)])
    def test_edit_message_invalid_text(self, new_message_text):
        message_id = self._add_message(self.user, self.operation, "author message")
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": new_message_text,
            "op_id": self.operation.id,
            "token": self.token
        })
        assert self._message_text(message_id) == "author message"
        assert self._events(sio, 'edit-message-client') == []

    def test_edit_message_emits_stored_text(self):
        message_id = self._add_message(self.user, self.operation, "author message")
        sio = self._connect(self.token)
        sio.emit('edit-message', {
            "message_id": str(message_id),
            "new_message_text": "x" * MAX_MESSAGE_TEXT_LENGTH,
            "op_id": str(self.operation.id),
            "token": self.token
        })
        assert self._message_text(message_id) == "x" * MAX_MESSAGE_TEXT_LENGTH
        events = self._events(sio, 'edit-message-client')
        assert [json.loads(msg["args"][0]) for msg in events] == [
            {"message_id": message_id, "new_message_text": "x" * MAX_MESSAGE_TEXT_LENGTH,
             "op_id": self.operation.id}]

    @pytest.mark.parametrize("payload", [
        {"reply_id": None}, {"reply_id": "abc"}, {"reply_id": 1.5}, {"reply_id": "missing"},
        {"message_text": None}, {"message_text": {}}, {"message_text": ""},
        {"message_text": "x" * (MAX_MESSAGE_TEXT_LENGTH + 1)}, {"op_id": None}, {"op_id": "missing"},
    ])
    def test_send_invalid_message(self, payload):
        message = {"op_id": self.operation.id, "token": self.token, "message_text": "invalid message",
                   "reply_id": -1}
        message.update(payload)
        message = {key: value for key, value in message.items() if value != "missing"}
        sio = self._connect(self.token)
        sio.emit("chat-message", message)
        assert sio.get_received() == []
        with self.app.app_context():
            assert Message.query.filter_by(op_id=self.operation.id).count() == 0

    def test_collaborator_can_not_delete_message_with_replies_of_others(self):
        # deleting a message deletes its replies, a collaborator may only delete their own
        collaborator_token = self._add_user_to_operation(self.anotheruserdata, self.operation_name, "collaborator")
        own_thread = self._add_message(self.anotheruser, self.operation, "own thread")
        own_reply = self._add_message(self.anotheruser, self.operation, "own reply", reply_id=own_thread)
        shared_thread = self._add_message(self.anotheruser, self.operation, "shared thread")
        other_reply = self._add_message(self.user, self.operation, "other reply", reply_id=shared_thread)
        sio = self._connect(self.token)
        for message_id in (own_thread, shared_thread):
            sio.emit('delete-message', {
                "message_id": message_id,
                "op_id": self.operation.id,
                "token": collaborator_token
            })
        assert self._message_text(own_thread) is None
        assert self._message_text(own_reply) is None
        assert self._message_text(shared_thread) == "shared thread"
        assert self._message_text(other_reply) == "other reply"
        assert [json.loads(msg["args"][0])["message_id"] for msg in self._events(sio, 'delete-message-client')] \
            == [own_thread]

    def test_admin_deletes_message_with_replies_of_others(self):
        thread = self._add_message(self.anotheruser, self.operation, "thread")
        reply = self._add_message(self.anotheruser, self.operation, "reply", reply_id=thread)
        sio = self._connect(self.token)
        sio.emit('delete-message', {
            "message_id": thread,
            "op_id": self.operation.id,
            "token": self.token
        })
        assert self._message_text(thread) is None
        assert self._message_text(reply) is None

    @pytest.mark.parametrize("message_type", [MessageType.TEXT, MessageType.SYSTEM_MESSAGE, 99, None])
    def test_upload_file_rejects_non_attachment_message_type(self, message_type):
        data = {
            "token": self.token,
            "op_id": self.operation.id,
            "file": open(icons('16x16'), 'rb'),
        }
        if message_type is not None:
            data["message_type"] = int(message_type)
        with self.app.test_client() as c:
            res = c.post("message_attachment", data=data, content_type="multipart/form-data")
        data["file"].close()
        assert res.json["success"] is False
        assert not os.path.exists(os.path.join(self.app.config['UPLOAD_FOLDER'], str(self.operation.id)))
        with self.app.app_context():
            assert Message.query.filter_by(op_id=self.operation.id).count() == 0

    def test_reply_only_to_top_level_message_of_same_operation(self):
        other_operation = self._new_operation("other", "other operation")
        self._add_user_to_operation(self.anotheruserdata, "other", "creator")
        foreign_id = self._add_message(self.anotheruser, other_operation, "foreign message")
        parent_id = self._add_message(self.user, self.operation, "parent message")
        reply_id = self._add_message(self.user, self.operation, "a reply", reply_id=parent_id)
        sio = self._connect(self.token)
        for target_id, text in ((foreign_id, "injected"), (reply_id, "nested"), (987654, "unknown"),
                                (parent_id, "valid reply")):
            sio.emit("chat-message", {
                "op_id": self.operation.id,
                "token": self.token,
                "message_text": text,
                "reply_id": target_id
            })
        with self.app.app_context():
            assert Message.query.filter(Message.text.in_(["injected", "nested", "unknown"])).count() == 0
            assert Message.query.filter_by(text="valid reply", reply_id=parent_id).count() == 1
            assert Message.query.filter_by(op_id=other_operation.id).count() == 1

    def _set_active(self, operation, active):
        with self.app.app_context():
            db.session.get(Operation, operation.id).active = active
            db.session.commit()

    def _save(self, sio, token, **extra):
        sio.emit('file-save', {"op_id": self.operation.id, "token": token, "content": XML_CONTENT1,
                               "comment": "XML_CONTENT1", **extra})

    def _refusals(self, sio):
        return [json.loads(event["args"][0]) for event in self._events(sio, SocketEvents.FILE_SAVE_REFUSED)]

    def test_file_save_of_viewer_is_refused_to_its_sender(self):
        with self.app.app_context():
            assert add_user_to_operation(path=self.operation_name, access_level="viewer",
                                         emailid=self.anotheruserdata[0])
        viewer = self._connect(self._another_token())
        member = self._connect(self.token)
        self._save(viewer, self._another_token())
        refusals = self._refusals(viewer)
        assert len(refusals) == 1
        assert refusals[0]["op_id"] == self.operation.id
        assert "access level is viewer" in refusals[0]["message"]
        # only its sender is told
        assert self._refusals(member) == []
        with self.app.app_context():
            assert self.fm.get_file(self.operation.id, self.user) == XML_CONTENT_INIT

    def test_file_save_with_too_long_version_name_is_refused(self):
        sio = self._connect(self.token)
        self._save(sio, self.token, version_name="x" * 256)
        refusals = self._refusals(sio)
        assert len(refusals) == 1
        assert "version name" in refusals[0]["message"]
        with self.app.app_context():
            # nothing was written, no half-done save
            assert self.fm.get_file(self.operation.id, self.user) == XML_CONTENT_INIT
            assert Change.query.filter_by(op_id=self.operation.id).count() == 0
            assert Message.query.filter_by(op_id=self.operation.id).count() == 0
        self._save(sio, self.token, version_name="x" * 255)
        assert self._refusals(sio) == []
        with self.app.app_context():
            assert Change.query.filter_by(op_id=self.operation.id).one().version_name == "x" * 255

    def test_archived_operation_chat_and_flight_track_are_read_only(self):
        message_id = self._add_message(self.user, self.operation, "written before archiving")
        self._set_active(self.operation, False)
        sio = self._connect(self.token)
        self._send(sio, "sent to archive")
        sio.emit('edit-message', {
            "message_id": message_id,
            "new_message_text": "rewritten",
            "op_id": self.operation.id,
            "token": self.token
        })
        sio.emit('delete-message', {
            "message_id": message_id,
            "op_id": self.operation.id,
            "token": self.token
        })
        sio.emit('file-save', {
            "op_id": self.operation.id,
            "token": self.token,
            "content": XML_CONTENT1,
            "comment": "XML_CONTENT1"
        })
        assert self._message_text(message_id) == "written before archiving"
        with self.app.app_context():
            assert Message.query.filter_by(op_id=self.operation.id).count() == 1
            assert Change.query.filter_by(op_id=self.operation.id).count() == 0
            assert self.fm.get_file(self.operation.id, self.user) == XML_CONTENT_INIT
        # the refused save is reported to its sender, nothing else is sent
        events = self._events(sio)
        assert [event["name"] for event in events] == [SocketEvents.FILE_SAVE_REFUSED]
        assert json.loads(events[0]["args"][0])["op_id"] == self.operation.id
        # once unarchived, the same requests change the operation
        self._set_active(self.operation, True)
        self._send(sio, "sent after unarchiving")
        sio.emit('file-save', {
            "op_id": self.operation.id,
            "token": self.token,
            "content": XML_CONTENT1,
            "comment": "XML_CONTENT1"
        })
        with self.app.app_context():
            assert Message.query.filter_by(text="sent after unarchiving").count() == 1
            assert Change.query.filter_by(op_id=self.operation.id).count() == 1
        assert len(self._events(sio, SocketEvents.FILE_CHANGED)) == 1

    def test_archived_operation_rejects_attachment(self):
        self._set_active(self.operation, False)
        sio = self._connect(self.token)
        data = {
            "token": self.token,
            "op_id": self.operation.id,
            "message_type": int(MessageType.IMAGE),
            "file": open(icons('16x16'), 'rb'),
        }
        with self.app.test_client() as c:
            res = c.post("message_attachment", data=data, content_type="multipart/form-data")
        data["file"].close()
        assert res.data == b"False"
        assert not os.path.exists(os.path.join(self.app.config['UPLOAD_FOLDER'], str(self.operation.id)))
        with self.app.app_context():
            assert Message.query.filter_by(op_id=self.operation.id).count() == 0
        assert self._events(sio) == []
