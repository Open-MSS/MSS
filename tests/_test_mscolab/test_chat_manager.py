# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_chat_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat_manager functionalities

    This file is part of MSS.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2023 by the MSS team, see AUTHORS.
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
import secrets
import pytest

from werkzeug.datastructures import FileStorage

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Operation, Message, MessageType
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation


class Test_Chat_Manager:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        _, self.cm, _ = mscolab_managers
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])
        with self.app.app_context():
            yield

    def test_add_message(self):
        with self.app.test_client():
            message = self.cm.add_message(self.user, 'some message',
                                          self.operation_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            assert message.text == 'some message'

    def test_edit_messages(self):
        with self.app.test_client():
            message = self.cm.add_message(self.user, 'some test message',
                                          self.operation_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            new_message_text = "Wonderland"
            self.cm.edit_message(message.id, new_message_text)
            message = Message.query.filter_by(id=message.id).first()
            assert message.text == new_message_text

    def test_delete_messages(self):
        with self.app.test_client():
            message = self.cm.add_message(self.user, 'some test example message',
                                          self.operation_name, message_type=MessageType.TEXT,
                                          reply_id=None)
            assert 'some test example message' in message.text
            self.cm.delete_message(message.id)
            message = Message.query.filter(Message.id == message.id).first()
            assert message is None

    def test_add_attachment(self):
        sample_path = os.path.join(os.path.dirname(__file__), "..", "data")
        filename = "example.csv"
        name, ext = filename.split('.')
        open_csv = os.path.join(sample_path, "example.csv")
        operation = Operation.query.filter_by(path=self.operation_name).first()
        token = secrets.token_urlsafe(16)
        with open(open_csv, 'rb') as fp:
            file = FileStorage(fp, filename=filename, content_type="text/csv")
            static_path = self.cm.add_attachment(operation.id, mscolab_settings.UPLOAD_FOLDER, file, token)
            assert name in static_path
            assert static_path.endswith(ext)
            assert token in static_path
