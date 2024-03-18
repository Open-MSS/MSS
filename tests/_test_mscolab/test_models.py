# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    api integration tests for models

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2022 by the MSS team, see AUTHORS.
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
import pytest
import datetime
import textwrap
from zoneinfo import ZoneInfo

from mslib.mscolab.server import register_user
from mslib.mscolab.models import AwareDateTime, User, Permission, Operation, Message, Change


def test_aware_datetime_conversion():
    aware_datetime_type = AwareDateTime()
    curr_time = datetime.datetime.now(tz=datetime.timezone.utc)

    result_bind = aware_datetime_type.process_bind_param(curr_time, None)
    assert result_bind is not None
    assert result_bind == curr_time

    result_result = aware_datetime_type.process_result_value(curr_time, None)
    assert result_result is not None
    assert result_result == curr_time

    result_none = aware_datetime_type.process_bind_param(None, None)
    assert result_none is None

    cet_time = datetime.datetime.now(tz=ZoneInfo("CET"))
    result_cet = aware_datetime_type.process_bind_param(cet_time, None)
    assert result_cet == cet_time
    assert result_cet is not None


def test_permission_creation():
    permission = Permission(1, 1, "admin")

    assert permission.u_id == 1
    assert permission.op_id == 1
    assert permission.access_level == "admin"


@pytest.mark.parametrize("access_level", ["collaborator", "viewer", "creator"])
def test_permission_repr_values(access_level):
    permission = Permission(1, 1, access_level)
    expected_repr = textwrap.dedent(f'''\
        <Permission u_id: {1}, op_id:{1}, access_level: {access_level}>''').strip()

    assert repr(permission).strip() == expected_repr


def test_operation_creation():
    operation = Operation("/path/to/operation", "Description of the operation", category="test_category")

    assert operation.path == "/path/to/operation"
    assert operation.description == "Description of the operation"
    assert operation.category == "test_category"
    assert operation.active is True


def test_operation_repr():
    operation = Operation("/path/to/operation", "Description of the operation", category="test_category")
    expected_repr = f'<Operation path: {"/path/to/operation"}, desc: {"Description of the operation"},' \
                    f' cat: {"test_category"}, active: True, ' \
                    f'last_used: {operation.last_used}> '

    assert repr(operation) == expected_repr


def test_message_creation():
    message = Message(1, 1, "Hello, this is a test message", "TEXT", None)

    assert message.op_id == 1
    assert message.u_id == 1
    assert message.text == "Hello, this is a test message"
    assert message.message_type == "TEXT"
    assert message.reply_id is None


def test_change_creation():
    change = Change(1, 1, "#abcdef123456", "v1.0", "Initial commit")

    assert change.op_id == 1
    assert change.u_id == 1
    assert change.commit_hash == "#abcdef123456"
    assert change.version_name == "v1.0"
    assert change.comment == "Initial commit"


class Test_User:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app):
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        with mscolab_app.app_context():
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[2])
            assert result["success"] is True
            yield

    def test_generate_auth_token(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        token = user.generate_auth_token()
        assert token is not None
        assert len(token) > 20

    def test_verify_auth_token(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        token = user.generate_auth_token()
        uid = user.verify_auth_token(token)
        assert user.id == uid

    def test_verify_password(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        assert user.verify_password("fail") is False
        assert user.verify_password(self.userdata[2]) is True
