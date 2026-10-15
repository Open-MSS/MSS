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
    GetAllChangesRequest, GetAllChangesResponse,
    GetOperationsRequest, GetOperationsResponse,
    GetCreatorOfOperationRequest, GetCreatorOfOperationResponse,
    LoginRequest, LoginResponse,
    MessageAttachmentResponse,
    TOKEN_HEADER,
)
from mslib.mscolab.auth import register_user
from mslib.mscolab.seed import XML_CONTENT_INIT
from mslib.mscolab.utils import ATTACHMENTS_URL_PREFIX


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

    def _get(self, endpoint, params):
        # msui sends the parameters in the query string and the token in a header; no body, as through a proxy
        # that drops the body of GET requests
        return self.client.get("/" + endpoint, query_string=params, headers={TOKEN_HEADER: self.token})

    def _create_operation(self, path="contract"):
        req = CreateOperationRequest(path=path, description="desc", content=XML_CONTENT_INIT)
        response = self._post(endpoints.CREATE_OPERATION, req.to_form_data())
        assert response.status_code == 200
        return response

    def _op_id(self, path="contract"):
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_params())
        return next(op.op_id for op in GetOperationsResponse.from_text(response.text).operations
                    if op.path == path)

    def test_plain_text_response(self):
        response = self._create_operation()
        assert response.text == "True"
        assert CreateOperationResponse.from_text(response.text).success is True

    def test_json_dumps_response(self):
        self._create_operation()
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_params())
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
        response = self._get(endpoints.GET_CREATOR_OF_OPERATION, req.to_params())
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        parsed = GetCreatorOfOperationResponse.from_text(response.text)
        assert parsed.success is True
        assert parsed.username == "contract"

    def test_auth_failed_response(self):
        self.token = "not-a-valid-token"
        response = self._get(endpoints.OPERATIONS, GetOperationsRequest().to_params())
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

    def test_get_all_changes_non_member(self):
        self._create_operation()
        op_id = self._op_id()
        register_user("outsider2@example.org", "secret", "outsider2", "Outsider")
        response = self.client.post(
            "/" + endpoints.TOKEN,
            data=LoginRequest(email="outsider2@example.org", password="secret").to_form_data())
        self.token = LoginResponse.from_text(response.text).token
        response = self._get(endpoints.GET_ALL_CHANGES, GetAllChangesRequest(op_id=op_id).to_params())
        assert response.status_code == 200
        assert GetAllChangesResponse.from_text(response.text) == GetAllChangesResponse(success=False, changes=[])

    def test_get_of_older_clients(self):
        # msui up to 11.x sent the token and the parameters of GET requests in the body
        self._create_operation()
        req = GetCreatorOfOperationRequest(op_id=self._op_id())
        response = self.client.get("/" + endpoints.GET_CREATOR_OF_OPERATION,
                                   data={"op_id": req.op_id, "token": self.token})
        assert response.status_code == 200
        assert GetCreatorOfOperationResponse.from_text(response.text).username == "contract"

    def test_header_token_takes_precedence(self):
        self._create_operation()
        response = self.client.get("/" + endpoints.OPERATIONS, headers={TOKEN_HEADER: "not-a-valid-token"},
                                   data={"token": self.token})
        assert response.text == "False"

    @pytest.mark.parametrize("params", [{}, {"op_id": "abc"}, {"op_id": "1.0"}, {"op_id": "1_0"},
                                        {"op_id": "100000000000000000000"}])
    def test_missing_or_non_integer_op_id(self, params):
        self._create_operation()
        for endpoint in (endpoints.GET_CREATOR_OF_OPERATION, endpoints.GET_ALL_CHANGES, endpoints.MESSAGES,
                         endpoints.AUTHORIZED_USERS, endpoints.ACTIVE_USERS, "operation_details"):
            response = self._get(endpoint, params)
            assert response.status_code == 400, endpoint
            assert response.text == "op_id must be an integer"

    @pytest.mark.parametrize("data", [{"op_id": "abc"}, {"op_id": "1", "days": "x"}])
    def test_set_last_used_non_integer_fields(self, data):
        response = self._post("set_last_used", data)
        assert response.status_code == 400

    def test_delete_bulk_permissions_malformed_user_ids(self):
        self._create_operation()
        response = self._post(endpoints.DELETE_BULK_PERMISSIONS, {"op_id": self._op_id(), "selected_userids": "abc"})
        assert response.status_code == 400
        assert response.text == "selected_userids must be a JSON list of integers"

    @pytest.mark.parametrize("name", ["abc", "1_0", "100000000000000000000"])
    def test_attachment_of_non_integer_operation(self, name):
        response = self.client.get(f"/{ATTACHMENTS_URL_PREFIX}/{name}/x.txt", headers={TOKEN_HEADER: self.token})
        assert response.status_code == 404

    def test_message_attachment_non_integer_op_id(self):
        # SQLite matched "1.0" to operation 1 and the file was stored in a folder "1.0" the attachment route refuses
        self._create_operation()
        response = self._post(endpoints.MESSAGE_ATTACHMENT, {"op_id": f"{self._op_id()}.0", "message_type": "2"})
        assert response.status_code == 400
