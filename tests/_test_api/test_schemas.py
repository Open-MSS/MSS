# -*- coding: utf-8 -*-
"""

    tests._test_api.test_schemas
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Round-trip tests for mslib.mscolab.api.schemas: for each dataclass,
    serialize -> parse -> compare. These only check each schema against
    itself; tests/_test_mscolab/test_api_contract.py checks the schemas
    against the real Flask routes.

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

from mslib.mscolab.api.schemas import (
    AUTH_FAILED_TEXT,
    AuthorizedUserInfo,
    BulkPermissionsRequest,
    BulkPermissionsResponse,
    ChangeInfo,
    ChatMessageInfo,
    CreateOperationRequest,
    CreateOperationResponse,
    DeleteBulkPermissionsRequest,
    DeleteBulkPermissionsResponse,
    DeleteOperationRequest,
    DeleteOperationResponse,
    DeleteOwnAccountResponse,
    FetchProfileImageRequest,
    GetActiveUsersRequest,
    GetActiveUsersResponse,
    GetAllChangesRequest,
    GetAllChangesResponse,
    GetAuthorizedUsersRequest,
    GetAuthorizedUsersResponse,
    GetChangeContentRequest,
    GetChangeContentResponse,
    GetCreatorOfOperationRequest,
    GetCreatorOfOperationResponse,
    GetMessagesRequest,
    GetMessagesResponse,
    GetOperationByIdRequest,
    GetOperationByIdResponse,
    GetOperationsRequest,
    GetOperationsResponse,
    GetOperationUsersRequest,
    GetOperationUsersResponse,
    GetUserResponse,
    IdpLoginAuthRequest,
    IdpLoginAuthResponse,
    IdpUserInfo,
    ImportPermissionsRequest,
    ImportPermissionsResponse,
    LoginRequest,
    LoginResponse,
    MessageAttachmentRequest,
    MessageAttachmentResponse,
    OperationInfo,
    ProfileImageMessageResponse,
    RegisterRequest,
    RegisterResponse,
    SetVersionNameRequest,
    SetVersionNameResponse,
    StatusResponse,
    UndoChangesRequest,
    UndoChangesResponse,
    UpdateOperationRequest,
    UpdateOperationResponse,
    UploadProfileImageRequest,
    UserInfo,
)


class Test_CreateOperationRequest:
    def test_round_trip_all_fields(self):
        req = CreateOperationRequest(
            path="my_operation", description="a description", category="mycat", content="<xml/>", active=False)
        assert CreateOperationRequest.from_form(req.to_form_data()) == req

    def test_round_trip_defaults(self):
        req = CreateOperationRequest(path="my_operation")
        assert CreateOperationRequest.from_form(req.to_form_data()) == req

    def test_to_form_data_omits_unset_optional_fields(self):
        req = CreateOperationRequest(path="my_operation")
        data = req.to_form_data()
        assert "description" not in data
        assert "content" not in data

    def test_from_form_matches_the_bare_request_form_reads_it_replaces(self):
        # Mirrors mslib.mscolab.blueprints.operation.create_operation's previous
        # manual request.form reads -- a plain dict stands in for Flask's
        # request.form here since from_form only uses __getitem__/get.
        form = {"path": "my_operation"}
        assert CreateOperationRequest.from_form(form) == CreateOperationRequest(path="my_operation")

    def test_from_form_requires_path(self):
        with pytest.raises(KeyError):
            CreateOperationRequest.from_form({})

    def test_active_string_encoding_round_trips(self):
        for active in (True, False):
            req = CreateOperationRequest(path="p", active=active)
            assert CreateOperationRequest.from_form(req.to_form_data()).active is active


class Test_CreateOperationResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = CreateOperationResponse(success=success)
        assert CreateOperationResponse.from_text(response.to_text()) == response

    def test_wire_format_is_unchanged(self):
        # The route used to return str(bool) directly; from_text/to_text must
        # keep producing/accepting exactly that, since older clients (and the
        # test helpers in tests/utils.py) still compare against "True"/"False".
        assert CreateOperationResponse(success=True).to_text() == "True"
        assert CreateOperationResponse(success=False).to_text() == "False"


class Test_OperationInfo:
    def test_round_trip(self):
        op = OperationInfo(
            op_id=1, access_level="creator", path="p", description="d", category="default", active=True)
        assert OperationInfo.from_dict(op.to_dict()) == op

    def test_from_dict_defaults_active_for_pre_8x_servers(self):
        # mslib.msui.mscolab.add_operations_to_ui has always tolerated servers
        # that don't send "active" at all (mscolab < 8.x) by assuming True.
        data = {"op_id": 1, "access_level": "creator", "path": "p", "description": None, "category": "default"}
        assert OperationInfo.from_dict(data).active is True


class Test_GetOperationsRequest:
    def test_round_trip(self):
        req = GetOperationsRequest(skip_archived=True)
        assert GetOperationsRequest.from_args_and_form({}, req.to_form_data()) == req

    def test_default(self):
        req = GetOperationsRequest()
        assert req.skip_archived is False
        assert GetOperationsRequest.from_args_and_form({}, {}) == req

    def test_args_take_precedence_over_form(self):
        # Mirrors the route's request.args.get(x, request.form.get(x, default)).
        parsed = GetOperationsRequest.from_args_and_form({"skip_archived": "True"}, {"skip_archived": "False"})
        assert parsed.skip_archived is True


class Test_GetOperationsResponse:
    def test_round_trip(self):
        response = GetOperationsResponse(operations=[
            OperationInfo(op_id=1, access_level="creator", path="a", description=None, category="default"),
            OperationInfo(op_id=2, access_level="collaborator", path="b", description="d", category="cat"),
        ])
        assert GetOperationsResponse.from_text(response.to_text()) == response

    def test_round_trip_empty(self):
        response = GetOperationsResponse(operations=[])
        assert GetOperationsResponse.from_text(response.to_text()) == response

    def test_manager_dicts_serialize_like_typed_entries(self):
        op = OperationInfo(op_id=1, access_level="creator", path="a", description=None, category="default")
        typed = GetOperationsResponse(operations=[op])
        assert GetOperationsResponse(operations=[op.to_dict()]).to_text() == typed.to_text()

    def test_auth_failure_sentinel(self):
        assert GetOperationsResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_GetOperationByIdRequest:
    def test_round_trip(self):
        req = GetOperationByIdRequest(op_id=42)
        assert GetOperationByIdRequest.from_args_and_form({}, req.to_form_data()) == req

    def test_missing_op_id_raises_like_the_bare_reads_did(self):
        with pytest.raises(TypeError):
            GetOperationByIdRequest.from_args_and_form({}, {})


class Test_GetOperationByIdResponse:
    def test_round_trip(self):
        response = GetOperationByIdResponse(content="<xml/>")
        assert GetOperationByIdResponse.from_text(response.to_text()) == response

    def test_auth_failure_sentinel(self):
        # Also covers fm.get_file() returning False (operation not found /
        # not a member) -- indistinguishable from an auth failure on the wire.
        assert GetOperationByIdResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_DeleteOperationRequest:
    def test_round_trip(self):
        req = DeleteOperationRequest(op_id=42)
        assert DeleteOperationRequest.from_form(req.to_form_data()) == req

    def test_missing_op_id_defaults_to_zero(self):
        assert DeleteOperationRequest.from_form({}) == DeleteOperationRequest(op_id=0)


class Test_DeleteOperationResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = DeleteOperationResponse(success=success, message="m")
        assert DeleteOperationResponse.from_text(response.to_text()) == response

    def test_to_dict_matches_to_text(self):
        # to_dict() feeds flask.jsonify() in the blueprint handler (keeps the
        # route's original application/json Content-Type); to_text() is what
        # the client parses. Both must describe the same wire shape.
        response = DeleteOperationResponse(success=True, message="m")
        assert response.to_dict() == json.loads(response.to_text())

    def test_auth_failure_sentinel(self):
        assert DeleteOperationResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_UpdateOperationRequest:
    def test_round_trip(self):
        req = UpdateOperationRequest(op_id=1, attribute="category", value="mycat")
        assert UpdateOperationRequest.from_form(req.to_form_data()) == req

    def test_from_form_requires_attribute_and_value(self):
        with pytest.raises(KeyError):
            UpdateOperationRequest.from_form({"op_id": 1})
        with pytest.raises(KeyError):
            UpdateOperationRequest.from_form({"op_id": 1, "attribute": "category"})

    def test_from_form_requires_op_id(self):
        with pytest.raises(TypeError):
            UpdateOperationRequest.from_form({"attribute": "category", "value": "mycat"})


class Test_UpdateOperationResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = UpdateOperationResponse(success=success)
        assert UpdateOperationResponse.from_text(response.to_text()) == response

    def test_wire_format_is_unchanged(self):
        assert UpdateOperationResponse(success=True).to_text() == "True"
        assert UpdateOperationResponse(success=False).to_text() == "False"


class Test_GetCreatorOfOperationRequest:
    def test_round_trip(self):
        req = GetCreatorOfOperationRequest(op_id=1)
        assert GetCreatorOfOperationRequest.from_args_and_form({}, req.to_form_data()) == req

    def test_op_id_is_not_cast_to_int(self):
        # Unlike the other op_id routes, this one passes op_id straight
        # through to the DB query untouched -- preserved, not "fixed", here.
        assert GetCreatorOfOperationRequest.from_args_and_form({}, {"op_id": "1"}).op_id == "1"


class Test_GetCreatorOfOperationResponse:
    def test_round_trip_success(self):
        response = GetCreatorOfOperationResponse(success=True, username="berta")
        assert GetCreatorOfOperationResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_failure(self):
        response = GetCreatorOfOperationResponse(success=False, message="You don't have access to this data")
        assert GetCreatorOfOperationResponse.from_text(json.dumps(response.to_dict())) == response

    def test_to_dict_only_includes_the_relevant_field(self):
        assert "message" not in GetCreatorOfOperationResponse(success=True, username="berta").to_dict()
        assert "username" not in GetCreatorOfOperationResponse(success=False, message="m").to_dict()


class Test_DeleteBulkPermissionsRequest:
    def test_round_trip(self):
        req = DeleteBulkPermissionsRequest(op_id=1, user_ids=[2, 3])
        assert DeleteBulkPermissionsRequest.from_form(req.to_form_data()) == req

    def test_round_trip_empty_user_ids(self):
        req = DeleteBulkPermissionsRequest(op_id=1, user_ids=[])
        assert DeleteBulkPermissionsRequest.from_form(req.to_form_data()) == req

    def test_missing_selected_userids_defaults_to_empty(self):
        assert DeleteBulkPermissionsRequest.from_form({"op_id": 1}) == DeleteBulkPermissionsRequest(
            op_id=1, user_ids=[])


class Test_DeleteBulkPermissionsResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = DeleteBulkPermissionsResponse(success=success, message="m")
        assert DeleteBulkPermissionsResponse.from_text(response.to_text()) == response

    def test_auth_failure_sentinel(self):
        assert DeleteBulkPermissionsResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_UserInfo:
    def test_round_trip(self):
        user = UserInfo(id=1, username="berta", fullname="Berta Test")
        assert UserInfo.from_dict(user.to_dict()) == user


class Test_GetUserResponse:
    def test_round_trip(self):
        response = GetUserResponse(user=UserInfo(id=1, username="berta", fullname="Berta Test"))
        assert GetUserResponse.from_text(response.to_text()) == response

    def test_auth_failure_sentinel(self):
        assert GetUserResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_LoginRequest:
    def test_round_trip(self):
        req = LoginRequest(email="berta@example.com", password="secret")
        assert LoginRequest.from_form(req.to_form_data()) == req

    def test_from_form_requires_email_and_password(self):
        with pytest.raises(KeyError):
            LoginRequest.from_form({"email": "berta@example.com"})


class Test_LoginResponse:
    def test_round_trip(self):
        response = LoginResponse(token="abc", user=UserInfo(id=1, username="berta", fullname="Berta Test"))
        assert LoginResponse.from_text(response.to_text()) == response

    def test_auth_failure_sentinel(self):
        assert LoginResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_UploadProfileImageRequest:
    def test_to_form_data(self):
        assert UploadProfileImageRequest(user_id=1).to_form_data() == {"user_id": 1}


class Test_FetchProfileImageRequest:
    def test_round_trip(self):
        req = FetchProfileImageRequest(user_id=1, op_id=2)
        assert FetchProfileImageRequest.from_args_and_form({}, req.to_form_data()) == req

    def test_op_id_defaults_to_none_and_is_omitted(self):
        req = FetchProfileImageRequest(user_id=1)
        data = req.to_form_data()
        assert "op_id" not in data
        assert FetchProfileImageRequest.from_args_and_form({}, data) == req


class Test_ProfileImageMessageResponse:
    def test_round_trip(self):
        response = ProfileImageMessageResponse(message="File too large")
        assert ProfileImageMessageResponse.from_text(json.dumps(response.to_dict())) == response


class Test_DeleteOwnAccountResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = DeleteOwnAccountResponse(success=success)
        assert DeleteOwnAccountResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert DeleteOwnAccountResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_GetOperationUsersRequest:
    def test_round_trip(self):
        req = GetOperationUsersRequest(op_id=1)
        assert GetOperationUsersRequest.from_args_and_form({}, req.to_form_data()) == req


class Test_GetOperationUsersResponse:
    def test_round_trip_success(self):
        response = GetOperationUsersResponse(success=True, users=[["berta", 1], ["carla", 2]])
        assert GetOperationUsersResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_failure(self):
        response = GetOperationUsersResponse(success=False, message="You don't have access to this data")
        assert GetOperationUsersResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert GetOperationUsersResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_BulkPermissionsRequest:
    def test_round_trip(self):
        req = BulkPermissionsRequest(op_id=1, user_ids=[2, 3], access_level="collaborator")
        assert BulkPermissionsRequest.from_form(req.to_form_data()) == req


class Test_BulkPermissionsResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = BulkPermissionsResponse(success=success, message="m")
        assert BulkPermissionsResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert BulkPermissionsResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_ImportPermissionsRequest:
    def test_round_trip(self):
        req = ImportPermissionsRequest(current_op_id=1, import_op_id=2)
        assert ImportPermissionsRequest.from_form(req.to_form_data()) == req


class Test_ImportPermissionsResponse:
    def test_round_trip_success_has_no_message(self):
        response = ImportPermissionsResponse(success=True)
        assert response.to_dict() == {"success": True}
        assert ImportPermissionsResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_failure(self):
        response = ImportPermissionsResponse(success=False, message="Some error occurred")
        assert ImportPermissionsResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert ImportPermissionsResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_AuthorizedUserInfo:
    def test_round_trip(self):
        user = AuthorizedUserInfo(username="berta", access_level="creator", id=1)
        assert AuthorizedUserInfo.from_dict(user.to_dict()) == user


class Test_GetAuthorizedUsersRequest:
    def test_round_trip(self):
        req = GetAuthorizedUsersRequest(op_id=1)
        assert GetAuthorizedUsersRequest.from_args_and_form({}, req.to_form_data()) == req


class Test_GetAuthorizedUsersResponse:
    def test_round_trip(self):
        response = GetAuthorizedUsersResponse(users=[
            AuthorizedUserInfo(username="berta", access_level="creator", id=1),
            AuthorizedUserInfo(username="carla", access_level="collaborator", id=2),
        ])
        assert GetAuthorizedUsersResponse.from_text(response.to_text()) == response

    def test_round_trip_empty(self):
        response = GetAuthorizedUsersResponse(users=[])
        assert GetAuthorizedUsersResponse.from_text(response.to_text()) == response

    def test_auth_failure_sentinel(self):
        assert GetAuthorizedUsersResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_GetActiveUsersRequest:
    def test_round_trip(self):
        req = GetActiveUsersRequest(op_id=1)
        assert GetActiveUsersRequest.from_args_and_form({}, req.to_form_data()) == req


class Test_GetActiveUsersResponse:
    def test_round_trip(self):
        response = GetActiveUsersResponse(active_users=[1, 2, 3])
        assert GetActiveUsersResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_empty(self):
        response = GetActiveUsersResponse(active_users=[])
        assert GetActiveUsersResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert GetActiveUsersResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_ChangeInfo:
    def test_round_trip(self):
        change = ChangeInfo(id=1, comment="c", version_name="v1", username="berta", created_at="2026-01-01T00:00:00")
        assert ChangeInfo.from_dict(change.to_dict()) == change

    def test_round_trip_no_comment_or_version_name(self):
        change = ChangeInfo(id=1, comment=None, version_name=None, username="berta", created_at="2026-01-01T00:00:00")
        assert ChangeInfo.from_dict(change.to_dict()) == change


class Test_GetAllChangesRequest:
    def test_round_trip(self):
        req = GetAllChangesRequest(op_id=1, named_version=True)
        assert GetAllChangesRequest.from_args_and_form(
            dict(pair.split("=") for pair in req.to_query_string().split("&")), req.to_form_data()) == req

    def test_query_string_is_separate_from_form_data(self):
        req = GetAllChangesRequest(op_id=1, named_version=True)
        assert "named_version" not in req.to_form_data()
        assert "op_id" not in req.to_query_string()


class Test_GetAllChangesResponse:
    def test_round_trip(self):
        response = GetAllChangesResponse(success=True, changes=[
            ChangeInfo(id=1, comment=None, version_name=None, username="berta", created_at="2026-01-01T00:00:00"),
        ])
        assert GetAllChangesResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert GetAllChangesResponse.from_text(AUTH_FAILED_TEXT) is None

    def test_to_dict_tolerates_the_bool_changes_bug(self):
        # See the pre-existing-bug NOTE on GetAllChangesResponse: the route
        # can send changes=false instead of a list. to_dict() must not crash
        # (jsonify itself never needed to iterate it either).
        response = GetAllChangesResponse(success=True, changes=False)
        assert response.to_dict() == {"success": True, "changes": False}

    def test_from_text_reproduces_the_bool_changes_crash(self):
        # ... but from_text() (client side) crashes the same way the
        # original `for change in changes:` loop would have.
        with pytest.raises(TypeError):
            GetAllChangesResponse.from_text(json.dumps({"success": True, "changes": False}))


class Test_GetChangeContentRequest:
    def test_round_trip(self):
        req = GetChangeContentRequest(ch_id=1)
        assert GetChangeContentRequest.from_args_and_form({}, req.to_form_data()) == req


class Test_GetChangeContentResponse:
    def test_round_trip(self):
        response = GetChangeContentResponse(content="<xml/>")
        assert GetChangeContentResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert GetChangeContentResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_SetVersionNameRequest:
    def test_round_trip(self):
        req = SetVersionNameRequest(op_id=1, ch_id=2, version_name="v1")
        assert SetVersionNameRequest.from_form(req.to_form_data()) == req

    def test_none_version_name_is_omitted(self):
        req = SetVersionNameRequest(op_id=1, ch_id=2, version_name=None)
        assert "version_name" not in req.to_form_data()
        assert SetVersionNameRequest.from_form(req.to_form_data()) == req


class Test_SetVersionNameResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = SetVersionNameResponse(success=success, message="m")
        assert SetVersionNameResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert SetVersionNameResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_UndoChangesRequest:
    def test_round_trip(self):
        req = UndoChangesRequest(ch_id=1)
        assert UndoChangesRequest.from_form(req.to_form_data()) == req

    def test_missing_ch_id_defaults_to_negative_one(self):
        assert UndoChangesRequest.from_form({}) == UndoChangesRequest(ch_id=-1)


class Test_UndoChangesResponse:
    @pytest.mark.parametrize("success", [True, False])
    def test_round_trip(self, success):
        response = UndoChangesResponse(success=success)
        assert UndoChangesResponse.from_text(response.to_text()) == response

    def test_wire_format_is_unchanged(self):
        assert UndoChangesResponse(success=True).to_text() == "True"
        assert UndoChangesResponse(success=False).to_text() == "False"


class Test_StatusResponse:
    def test_round_trip(self):
        response = StatusResponse(message="Mscolab server", use_saml2=True, direct_login=False)
        assert StatusResponse.from_text(json.dumps(response.to_dict())) == response

    def test_defaults_on_missing_keys(self):
        # Mirrors mscolab_connect_dialog.py's independent try/except defaults:
        # use_saml2 -> False, direct_login -> True when the key is absent.
        response = StatusResponse.from_text(json.dumps({"message": "Mscolab server"}))
        assert response.use_saml2 is False
        assert response.direct_login is True

    def test_defaults_on_invalid_json(self):
        response = StatusResponse.from_text("not json")
        assert response == StatusResponse(message="", use_saml2=False, direct_login=True)


class Test_RegisterRequest:
    def test_round_trip(self):
        req = RegisterRequest(email="berta@example.com", password="secret", username="berta", fullname="Berta Test")
        assert RegisterRequest.from_form(req.to_form_data()) == req

    def test_from_form_requires_all_fields(self):
        with pytest.raises(KeyError):
            RegisterRequest.from_form({"email": "berta@example.com"})


class Test_RegisterResponse:
    def test_round_trip_with_message(self):
        response = RegisterResponse(success=False, message="This email ID is already taken!")
        assert RegisterResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_without_message(self):
        response = RegisterResponse(success=True)
        assert response.to_dict() == {"success": True}
        assert RegisterResponse.from_text(json.dumps(response.to_dict())) == response


class Test_IdpLoginAuthRequest:
    def test_round_trip(self):
        req = IdpLoginAuthRequest(token="abc")
        assert IdpLoginAuthRequest.from_json_data(req.to_json_data()) == req


class Test_IdpUserInfo:
    def test_round_trip(self):
        user = IdpUserInfo(username="berta", id=1, emailid="berta@example.com")
        assert IdpUserInfo.from_dict(user.to_dict()) == user


class Test_IdpLoginAuthResponse:
    def test_round_trip_success(self):
        response = IdpLoginAuthResponse(
            success=True, token="abc", user=IdpUserInfo(username="berta", id=1, emailid="berta@example.com"))
        assert IdpLoginAuthResponse.from_text(response.to_text()) == response

    def test_round_trip_failure(self):
        response = IdpLoginAuthResponse(success=False)
        assert IdpLoginAuthResponse.from_text(json.dumps(response.to_dict())) == response

    def test_to_dict_omits_token_and_user(self):
        assert IdpLoginAuthResponse(success=False).to_dict() == {"success": False}


class Test_ChatMessageInfo:
    def test_round_trip_without_replies(self):
        message = ChatMessageInfo(
            id=1, u_id=2, username="berta", text="hi", message_type=0, reply_id=None,
            replies=[], time="2026-01-01T00:00:00")
        assert ChatMessageInfo.from_dict(message.to_dict()) == message

    def test_round_trip_with_replies(self):
        reply = ChatMessageInfo(
            id=2, u_id=3, username="carla", text="hi back", message_type=0, reply_id=1,
            replies=[], time="2026-01-01T00:01:00")
        message = ChatMessageInfo(
            id=1, u_id=2, username="berta", text="hi", message_type=0, reply_id=None,
            replies=[reply], time="2026-01-01T00:00:00")
        assert ChatMessageInfo.from_dict(message.to_dict()) == message


class Test_GetMessagesRequest:
    def test_round_trip(self):
        req = GetMessagesRequest(op_id=1, timestamp="2026-01-01T00:00:00+00:00")
        assert GetMessagesRequest.from_args_and_form({}, req.to_form_data()) == req

    def test_default_timestamp(self):
        req = GetMessagesRequest(op_id=1)
        assert req.timestamp == "1970-01-01T00:00:00+00:00"
        assert GetMessagesRequest.from_args_and_form({}, {"op_id": 1}) == req


class Test_GetMessagesResponse:
    def test_round_trip(self):
        response = GetMessagesResponse(messages=[
            ChatMessageInfo(
                id=1, u_id=2, username="berta", text="hi", message_type=0, reply_id=None,
                replies=[], time="2026-01-01T00:00:00"),
        ])
        assert GetMessagesResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_empty(self):
        response = GetMessagesResponse(messages=[])
        assert GetMessagesResponse.from_text(json.dumps(response.to_dict())) == response

    def test_auth_failure_sentinel(self):
        assert GetMessagesResponse.from_text(AUTH_FAILED_TEXT) is None


class Test_MessageAttachmentRequest:
    def test_round_trip(self):
        req = MessageAttachmentRequest(op_id=1, message_type=2)
        assert MessageAttachmentRequest.from_form(req.to_form_data()) == req

    def test_missing_message_type_parses_to_none(self):
        assert MessageAttachmentRequest.from_form({"op_id": "1"}).message_type is None


class Test_MessageAttachmentResponse:
    def test_round_trip_success(self):
        response = MessageAttachmentResponse(success=True, path="uploads/1/foo.png")
        assert MessageAttachmentResponse.from_text(json.dumps(response.to_dict())) == response

    def test_round_trip_failure_with_message(self):
        response = MessageAttachmentResponse(success=False, message="Could not send message. No file uploaded.")
        assert MessageAttachmentResponse.from_text(json.dumps(response.to_dict())) == response

    def test_to_dict_omits_unset_fields(self):
        assert MessageAttachmentResponse(success=True, path="p").to_dict() == {"success": True, "path": "p"}

    def test_auth_failure_sentinel(self):
        assert MessageAttachmentResponse.from_text(AUTH_FAILED_TEXT) is None
