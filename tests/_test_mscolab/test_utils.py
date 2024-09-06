# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab/utils

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
import datetime
import os
import pytest
import json

from fs.tempfs import TempFS
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Operation, Message, MessageType, User
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.utils import (get_recent_op_id, get_session_id,
                                 get_message_dict, create_files,
                                 os_fs_create_dir, get_user_id)


class Test_Utils:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        _, _, self.fm = mscolab_managers
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        with self.app.app_context():
            yield

    def test_get_recent_oid(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2])
        with self.app.test_client() as test_client:
            user = get_user(self.userdata[0])
            anotheruser = get_user(self.anotheruserdata[0])
            operation, token = self._create_operation(test_client, self.userdata)
            op_id = get_recent_op_id(self.fm, user)
            assert op_id == operation.id
            op_id = get_recent_op_id(self.fm, anotheruser)
            assert op_id is None

    def test_get_session_id(self):
        sockets = [{"u_id": 5, "s_id": 100}]
        assert get_session_id(sockets, 5) == 100

    def test_get_user_id(self):
        sockets = [{"u_id": 9, "s_id": 101}]
        assert get_user_id(sockets, 101) == 9

    def test_get_message_dict(self):
        message = Message(0, 0, "Moin")
        message.user = User(*self.userdata)
        message.created_at = datetime.datetime.now(tz=datetime.timezone.utc)
        result = get_message_dict(message)
        assert result["message_type"] == MessageType.TEXT

    def test_os_fs_create_dir(self):
        _fs = TempFS(identifier="msui")
        _dir = _fs.getsyspath("")
        os_fs_create_dir(_dir)
        assert os.path.exists(_dir)

    def test_create_file(self):
        create_files()
        # ToDo refactor to fs
        assert os.path.exists(mscolab_settings.OPERATIONS_DATA)
        assert os.path.exists(mscolab_settings.UPLOAD_FOLDER)

    def _create_operation(self, test_client, userdata=None, path="firstflight", description="simple test"):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        data = json.loads(response.data.decode('utf-8'))
        token = data["token"]
        response = test_client.post('/create_operation', data={"token": token,
                                                               "path": path,
                                                               "description": description})
        assert response.status_code == 200
        assert response.data.decode('utf-8') == "True"
        operation = Operation.query.filter_by(path=path).first()
        return operation, token
