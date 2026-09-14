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

from mslib.mscolab.events import SocketEvents
from mslib.mscolab.seed import (add_operation, add_user, add_user_to_operation, archive_operation,
                                delete_operation, delete_user, get_operation, get_user)


class Test_CliNotify:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_server):
        self.app = mscolab_app
        self.server_url = mscolab_server
        # the test server runs on a random port, not the SERVER_URL default
        self.app.config['SERVER_URL'] = self.server_url
        self.userdata = 'clinotify@example.org', 'clinotify', 'pw', 'CLI Notify User'
        assert add_user(*self.userdata)
        self.user = get_user(self.userdata[0])
        assert add_operation("cli_notify_op", "test op for cli notify")
        self.operation = get_operation("cli_notify_op")

    def _connect(self):
        sio = socketio.Client()
        sio.connect(self.server_url, wait_timeout=10)
        return sio

    def _wait_for(self, received, timeout=5):
        deadline = time.time() + timeout
        while not received and time.time() < deadline:
            time.sleep(0.05)
        return received

    def test_delete_user_notifies_revoke_permission(self):
        assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0])
        op_id, u_id = self.operation.id, self.user.id
        sio = self._connect()
        revoked, updated = [], []
        sio.on(SocketEvents.REVOKE_PERMISSION, handler=lambda data: revoked.append(json.loads(data)))
        sio.on(SocketEvents.OPERATION_PERMISSIONS_UPDATED, handler=lambda data: updated.append(json.loads(data)))
        try:
            assert delete_user(self.userdata[0])
            self._wait_for(revoked)
            self._wait_for(updated)
            assert revoked and revoked[0] == {"op_id": op_id, "u_id": u_id}
            assert updated and updated[0] == {"op_id": op_id, "u_id": u_id}
        finally:
            sio.disconnect()

    def test_delete_operation_notifies_operation_deleted(self):
        op_id = self.operation.id
        sio = self._connect()
        deleted = []
        sio.on(SocketEvents.OPERATION_DELETED, handler=lambda data: deleted.append(json.loads(data)))
        try:
            assert delete_operation("cli_notify_op")
            self._wait_for(deleted)
            assert deleted and deleted[0] == {"op_id": op_id}
        finally:
            sio.disconnect()

    def test_add_user_to_operation_notifies_new_permission(self):
        op_id, u_id = self.operation.id, self.user.id
        sio = self._connect()
        added = []
        sio.on(SocketEvents.NEW_PERMISSION, handler=lambda data: added.append(json.loads(data)))
        try:
            assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0])
            self._wait_for(added)
            assert added and added[0] == {"op_id": op_id, "u_id": u_id}
        finally:
            sio.disconnect()

    def test_archive_operation_notifies_operation_list_update(self):
        assert add_user_to_operation(path="cli_notify_op", emailid=self.userdata[0], access_level="creator")
        sio = self._connect()
        updated = []
        sio.on(SocketEvents.UPDATE_OPERATION_LIST, handler=lambda: updated.append(True))
        try:
            archive_operation(path="cli_notify_op", emailid=self.userdata[0])
            self._wait_for(updated)
            assert updated
        finally:
            sio.disconnect()

    def test_internal_notify_rejects_wrong_token(self):
        response = requests.post(
            f"{self.server_url}/internal_notify",
            data={"event": SocketEvents.OPERATION_DELETED, "op_id": self.operation.id, "token": "wrong-token"},
            timeout=5,
        )
        assert response.status_code == 401

    def test_internal_notify_rejects_non_local_requests(self):
        with self.app.test_client() as client:
            response = client.post(
                "/internal_notify",
                data={"event": SocketEvents.OPERATION_DELETED, "op_id": self.operation.id,
                      "token": self.app.config['ADMIN_TOKEN']},
                environ_overrides={"REMOTE_ADDR": "203.0.113.5"},
            )
        assert response.status_code == 401
