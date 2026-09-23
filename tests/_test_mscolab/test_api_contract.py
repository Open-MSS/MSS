# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_api_contract
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Checks that real server responses parse with the client-side schemas
    of mslib.mscolab.api, one test per response shape.

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

import pytest

from mslib.mscolab.api import endpoints
from mslib.mscolab.api.schemas import (
    CreateOperationRequest, CreateOperationResponse,
    GetOperationsRequest, GetOperationsResponse,
    GetCreatorOfOperationRequest, GetCreatorOfOperationResponse,
    LoginRequest, LoginResponse,
    MessageAttachmentResponse,
)
from mslib.mscolab.auth import register_user
from mslib.mscolab.seed import XML_CONTENT_INIT


class Test_ApiContract:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app):
        self.app = mscolab_app
        self.client = mscolab_app.test_client()
        with self.app.app_context():
            register_user("contract@example.org", "secret", "contract", "Contract User")
            response = self.client.post(
                "/" + endpoints.TOKEN,
                data=LoginRequest(email="contract@example.org", password="secret").to_form_data())
            assert response.status_code == 200
            self.token = LoginResponse.from_text(response.text).token
            yield

    def _post(self, endpoint, data):
        return self.client.post("/" + endpoint, data=data | {"token": self.token})

    def _get(self, endpoint, data):
        # the client's request_get() sends its payload in the request body, not the query string
        return self.client.get("/" + endpoint, data=data | {"token": self.token})

    def _create_operation(self, path="contract"):
        req = CreateOperationRequest(path=path, description="desc", content=XML_CONTENT_INIT)
        response = self._post(endpoints.CREATE_OPERATION, req.to_form_data())
        assert response.status_code == 200
        return response

    def _op_id(self, path="contract"):
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_form_data())
        return next(op.op_id for op in GetOperationsResponse.from_text(response.text).operations
                    if op.path == path)

    def test_plain_text_response(self):
        response = self._create_operation()
        assert response.text == "True"
        assert CreateOperationResponse.from_text(response.text).success is True

    def test_json_dumps_response(self):
        self._create_operation()
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_form_data())
        assert response.status_code == 200
        parsed = GetOperationsResponse.from_text(response.text)
        assert [op.path for op in parsed.operations] == ["contract"]
        op = parsed.operations[0]
        assert isinstance(op.op_id, int)
        assert op.access_level == "creator"
        assert op.active is True
        # every field the server sends is modelled by the schema
        assert set(json.loads(response.text)["operations"][0]) == set(op.to_dict())

    def test_jsonify_response(self):
        self._create_operation()
        req = GetCreatorOfOperationRequest(op_id=self._op_id())
        response = self._get(endpoints.GET_CREATOR_OF_OPERATION, req.to_form_data())
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        parsed = GetCreatorOfOperationResponse.from_text(response.text)
        assert parsed.success is True
        assert parsed.username == "contract"

    def test_auth_failed_response(self):
        self.token = "not-a-valid-token"
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_form_data())
        assert response.text == "False"
        assert GetOperationsResponse.from_text(response.text) is None

    def test_message_attachment_non_member_without_message_type(self):
        self._create_operation()
        op_id = self._op_id()
        register_user("outsider@example.org", "secret", "outsider", "Outsider")
        response = self.client.post(
            "/" + endpoints.TOKEN,
            data=LoginRequest(email="outsider@example.org", password="secret").to_form_data())
        self.token = LoginResponse.from_text(response.text).token
        response = self._post(endpoints.MESSAGE_ATTACHMENT, {"op_id": op_id})
        assert response.status_code == 200
        assert MessageAttachmentResponse.from_text(response.text) is None
