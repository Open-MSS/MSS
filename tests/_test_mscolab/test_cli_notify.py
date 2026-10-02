# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_cli_notify
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests that mscolab CLI actions (mslib.mscolab.seed) notify connected
    clients through the running server, since the CLI itself has no access
    to the live socket connections (issue #1389)

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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
import time

import pytest
import requests
import socketio

from mslib.mscolab.api.events import SocketEvents
from mslib.mscolab.cli_notify import notify_socket_event
from mslib.mscolab.seed import (add_all_users_default_operation, add_operation, add_user, add_user_to_operation,
                                archive_operation, delete_operation, delete_user, get_operation, get_user)


class Test_CliNotify:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_server_app, mscolab_server):
        # the app of the server, the sockets authenticate against its database
        self.app = mscolab_server_app
        self.server_url = mscolab_server
        # the test server runs on a random port, not the SERVER_URL default
        self.app.config['SERVER_URL'] = self.server_url
        self.userdata = 'clinotify@example.org', 'clinotify', 'pw', 'CLI Notify User'
        with self.app.app_context():
            assert add_user(*self.userdata)
            self.user_id = get_user(self.userdata[0]).id
            assert add_operation("cli_notify_op", "test op for cli notify")
            self.op_id = get_operation("cli_notify_op").id
        # events of an operation only reach its members, a second member watches them
        self.watcherdata = 'clinotify_watcher@example.org', 'clinotify_watcher', 'pw', 'CLI Notify Watcher'
        with self.app.app_context():
            assert add_user(*self.watcherdata)
            assert add_user_to_operation(path="cli_notify_op", emailid=self.watcherdata[0])

    def _token(self, emailid):
        with self.app.app_context():
            return get_user(emailid).generate_auth_token()

    def _connect(self, emailid=None):
        sio = socketio.Client()
        sio.connect(self.server_url, auth={"token": self._token(emailid or self.watcherdata[0])}, wait_timeout=10)
        return sio

    def _wait_for(self, received, timeout=5):
        deadline = time.time() + timeout
        while not received and time.time() < deadline:
            time.sleep(0.05)
        return received

    def test_delete_user_notifies_revoke_permission(self):
        with self.app.app_context():
            assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0])
        op_id, u_id = self.op_id, self.user_id
        sio = self._connect()
        user_sio = self._connect(self.userdata[0])
        revoked, updated, user_revoked = [], [], []
        sio.on(SocketEvents.REVOKE_PERMISSION, handler=lambda data: revoked.append(json.loads(data)))
        sio.on(SocketEvents.OPERATION_PERMISSIONS_UPDATED, handler=lambda data: updated.append(json.loads(data)))
        user_sio.on(SocketEvents.REVOKE_PERMISSION, handler=lambda data: user_revoked.append(json.loads(data)))
        try:
            with self.app.app_context():
                assert delete_user(self.userdata[0])
            self._wait_for(revoked)
            self._wait_for(updated)
            self._wait_for(user_revoked)
            assert revoked and revoked[0] == {"op_id": op_id, "u_id": u_id}
            assert updated and updated[0] == {"op_id": op_id, "u_id": u_id}
            # the removed user is told too, before leaving the room of the operation
            assert user_revoked and user_revoked[0] == {"op_id": op_id, "u_id": u_id}
            # a new account can get the same id on SQLite, its permissions must not reach the old socket
            user_new = []
            user_sio.on(SocketEvents.NEW_PERMISSION, handler=lambda data: user_new.append(json.loads(data)))
            with self.app.app_context():
                assert notify_socket_event(SocketEvents.NEW_PERMISSION, u_id=u_id, op_id=op_id)
            time.sleep(0.5)
            assert user_new == []
        finally:
            sio.disconnect()
            user_sio.disconnect()

    def test_delete_operation_notifies_operation_deleted(self):
        op_id = self.op_id
        sio = self._connect()
        deleted = []
        sio.on(SocketEvents.OPERATION_DELETED, handler=lambda data: deleted.append(json.loads(data)))
        try:
            with self.app.app_context():
                assert delete_operation("cli_notify_op")
            self._wait_for(deleted)
            assert deleted and deleted[0] == {"op_id": op_id}
        finally:
            sio.disconnect()

    def test_add_user_to_operation_notifies_new_permission(self):
        op_id, u_id = self.op_id, self.user_id
        sio = self._connect()
        # the added user is not yet a member when connecting, their socket joins the room with the permission
        user_sio = self._connect(self.userdata[0])
        added, user_added, user_deleted = [], [], []
        sio.on(SocketEvents.NEW_PERMISSION, handler=lambda data: added.append(json.loads(data)))
        user_sio.on(SocketEvents.NEW_PERMISSION, handler=lambda data: user_added.append(json.loads(data)))
        user_sio.on(SocketEvents.OPERATION_DELETED, handler=lambda data: user_deleted.append(json.loads(data)))
        try:
            with self.app.app_context():
                assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0])
            self._wait_for(added)
            self._wait_for(user_added)
            assert added and added[0] == {"op_id": op_id, "u_id": u_id}
            assert user_added and user_added[0] == {"op_id": op_id, "u_id": u_id}
            # and it gets the later events of the operation
            with self.app.app_context():
                assert delete_operation("cli_notify_op")
            self._wait_for(user_deleted)
            assert user_deleted == [{"op_id": op_id}]
        finally:
            sio.disconnect()
            user_sio.disconnect()

    def test_add_all_users_notifies_new_permission(self):
        op_id, u_id = self.op_id, self.user_id
        user_sio = self._connect(self.userdata[0])
        user_added, user_deleted = [], []
        user_sio.on(SocketEvents.NEW_PERMISSION, handler=lambda data: user_added.append(json.loads(data)))
        user_sio.on(SocketEvents.OPERATION_DELETED, handler=lambda data: user_deleted.append(json.loads(data)))
        try:
            with self.app.app_context():
                assert add_all_users_default_operation(path="cli_notify_op", access_level="collaborator")
            self._wait_for(user_added)
            assert {"op_id": op_id, "u_id": u_id} in user_added
            # the socket of the new member has joined the room of the operation
            with self.app.app_context():
                assert delete_operation("cli_notify_op")
            self._wait_for(user_deleted)
            assert user_deleted == [{"op_id": op_id}]
        finally:
            user_sio.disconnect()

    def test_operation_events_only_reach_members(self):
        # H1: a user who is not a member of the operation gets none of its events
        outsiderdata = 'clinotify_outsider@example.org', 'clinotify_outsider', 'pw', 'CLI Notify Outsider'
        with self.app.app_context():
            assert add_user(*outsiderdata)
        sio = self._connect()
        outsider_sio = self._connect(outsiderdata[0])
        deleted, outsider_events = [], []
        sio.on(SocketEvents.OPERATION_DELETED, handler=lambda data: deleted.append(json.loads(data)))
        outsider_sio.on("*", handler=lambda event, *args: outsider_events.append(event))
        try:
            with self.app.app_context():
                assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0])
                assert delete_operation("cli_notify_op")
            self._wait_for(deleted)
            assert deleted == [{"op_id": self.op_id}]
            # the events are emitted in order, so the outsider would have got them by now
            time.sleep(0.5)
            assert outsider_events == []
        finally:
            sio.disconnect()
            outsider_sio.disconnect()

    def test_connection_with_invalid_token_is_refused(self):
        sio = socketio.Client()
        with pytest.raises(socketio.exceptions.ConnectionError):
            sio.connect(self.server_url, auth={"token": "invalid"}, wait_timeout=10)

    def test_connection_without_token_gets_no_operation_events(self):
        # older msui clients connect without a token, they are accepted but join no operation room
        sio = socketio.Client()
        sio.connect(self.server_url, wait_timeout=10)
        watcher = self._connect()
        events, deleted = [], []
        sio.on("*", handler=lambda event, *args: events.append(event))
        watcher.on(SocketEvents.OPERATION_DELETED, handler=lambda data: deleted.append(json.loads(data)))
        try:
            with self.app.app_context():
                assert delete_operation("cli_notify_op")
            self._wait_for(deleted)
            assert deleted == [{"op_id": self.op_id}]
            time.sleep(0.5)
            assert events == []
        finally:
            sio.disconnect()
            watcher.disconnect()

    def test_archive_operation_notifies_operation_list_update(self):
        with self.app.app_context():
            assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0], access_level="creator")
        sio = self._connect()
        updated = []
        sio.on(SocketEvents.UPDATE_OPERATION_LIST, handler=lambda: updated.append(True))
        try:
            with self.app.app_context():
                archive_operation(path="cli_notify_op", emailid=self.userdata[0])
            self._wait_for(updated)
            assert updated
        finally:
            sio.disconnect()

    def test_internal_notify_rejects_wrong_token(self):
        response = requests.post(
            f"{self.server_url}/internal_notify",
            data={"event": SocketEvents.OPERATION_DELETED, "op_id": self.op_id, "token": "wrong-token"},
            timeout=5,
        )
        assert response.status_code == 401

    def test_internal_notify_rejects_non_local_requests(self):
        with self.app.test_client() as client:
            response = client.post(
                "/internal_notify",
                data={"event": SocketEvents.OPERATION_DELETED, "op_id": self.op_id,
                      "token": self.app.config['ADMIN_TOKEN']},
                environ_overrides={"REMOTE_ADDR": "203.0.113.5"},
            )
        assert response.status_code == 401
