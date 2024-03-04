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

from mslib.mscolab.server import register_user
from mslib.mscolab.models import AwareDateTime, User, Permission, Operation, Message, Change


class Test_AwareDateTime:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.aware_datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    def test_aware_datetime_conversion(self):
        aware_datetime_type = AwareDateTime()

        result_bind = aware_datetime_type.process_bind_param(self.aware_datetime, None)
        assert result_bind == self.aware_datetime

        result_result = aware_datetime_type.process_result_value(self.aware_datetime, None)
        assert result_result == self.aware_datetime


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


class Test_Permission:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.u_id = 1
        self.op_id = 1
        self.access_level = "admin"

    def test_permission_creation(self):
        permission = Permission(self.u_id, self.op_id, self.access_level)

        assert permission.u_id == self.u_id
        assert permission.op_id == self.op_id
        assert permission.access_level == self.access_level


class Test_Operation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.path = "/path/to/operation"
        self.description = "Description of the operation"
        self.category = "test_category"

    def test_operation_creation(self):
        operation = Operation(self.path, self.description, category=self.category)

        assert operation.path == self.path
        assert operation.description == self.description
        assert operation.category == self.category
        assert operation.active is True


class Test_Message:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.op_id = 1
        self.u_id = 1
        self.text = "Hello, this is a test message"
        self.message_type = "TEXT"
        self.reply_id = None

    def test_message_creation(self):
        message = Message(
            self.op_id,
            self.u_id,
            self.text,
            message_type=self.message_type,
            reply_id=self.reply_id
        )

        assert message.op_id == self.op_id
        assert message.u_id == self.u_id
        assert message.text == self.text
        assert message.message_type == self.message_type
        assert message.reply_id == self.reply_id


class Test_Change:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.op_id = 1
        self.u_id = 1
        self.commit_hash = "#abcdef123456"
        self.version_name = "v1.0"
        self.comment = "Initial commit"

    def test_change_creation(self):
        change = Change(self.op_id,
                        self.u_id,
                        self.commit_hash,
                        version_name=self.version_name,
                        comment=self.comment
                    )

        assert change.op_id == self.op_id
        assert change.u_id == self.u_id
        assert change.commit_hash == self.commit_hash
        assert change.version_name == self.version_name
        assert change.comment == self.comment
