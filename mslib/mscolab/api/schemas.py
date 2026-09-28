# -*- coding: utf-8 -*-
"""

    mslib.mscolab.api.schemas
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Request/response dataclasses for mscolab REST routes. Each dataclass
    owns both directions of its wire format (building the form-encoded dict
    the client posts / parsing the Flask request.form on the server; building
    the response text / parsing it back on the client), so a field rename is
    a single-point change instead of two independent, silently-divergent
    dict literals.

    Only migrated routes have a schema here -- see endpoints.py for which
    ones. This is stdlib dataclasses only (Python <3.12 pin, no new runtime
    dependency). The type hints are documentation for readers and IDEs
    only: nothing checks them at runtime, and ``op_id: object`` marks
    fields the server does not convert to int. tests/_test_api/ only checks
    each schema against itself;
    tests/_test_mscolab/test_api_contract.py checks schemas against the real
    Flask routes.

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
from dataclasses import dataclass, field
from typing import List, Optional, Union
from urllib.parse import urlencode

# mslib.mscolab.auth.verify_user (the @verify_user decorator wrapping every
# authenticated route) returns this bare, non-JSON string -- instead of
# calling the route at all -- whenever the token is missing/invalid. Every
# response schema below that wraps a @verify_user route has to recognize it
# as a distinct case from its normal JSON body; from_text() returns None for
# it rather than raising a JSON-decode error, matching what the routes have
# always actually done on the wire.
AUTH_FAILED_TEXT = "False"


def _record_dict(record):
    # Server routes pass the managers' plain dicts through unchanged, so list
    # responses serialize either a typed record or the dict it models.
    return record.to_dict() if hasattr(record, "to_dict") else record


@dataclass
class CreateOperationRequest:
    """POST endpoints.CREATE_OPERATION -- create a new operation."""

    path: str
    description: Optional[str] = None
    category: str = "default"
    content: Optional[str] = None
    active: bool = True

    def to_form_data(self):
        """Build the form-encoded dict mslib.msui.mscolab posts to the server."""
        data = {"path": self.path, "category": self.category, "active": str(self.active)}
        if self.description is not None:
            data["description"] = self.description
        if self.content is not None:
            data["content"] = self.content
        return data

    @classmethod
    def from_form(cls, form):
        """Parse an incoming Flask request.form into a typed request.

        Raises the same exception a bare ``request.form["path"]`` would
        (missing required field), so the handler's existing 400 behaviour is
        unchanged.
        """
        return cls(
            path=form["path"],
            description=form.get("description", None),
            category=form.get("category", "default"),
            content=form.get("content", None),
            active=form.get("active", "True") == "True",
        )


@dataclass
class CreateOperationResponse:
    """Response body for POST endpoints.CREATE_OPERATION: plain-text "True"/"False"."""

    success: bool

    def to_text(self):
        return str(self.success)

    @classmethod
    def from_text(cls, text):
        return cls(success=(text == "True"))


@dataclass
class OperationInfo:
    """One entry of GetOperationsResponse.operations -- mirrors the dict
    mslib.mscolab.file_manager.FileManager.list_operations builds per row.
    """

    op_id: int
    access_level: str
    path: str
    description: Optional[str]
    category: str
    active: bool = True

    def to_dict(self):
        return {
            "op_id": self.op_id,
            "access_level": self.access_level,
            "path": self.path,
            "description": self.description,
            "category": self.category,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            op_id=data["op_id"],
            access_level=data["access_level"],
            path=data["path"],
            description=data["description"],
            category=data["category"],
            # mslib.msui.mscolab.add_operations_to_ui has always defaulted this
            # to True for compatibility with servers older than 8.x that don't
            # send "active" at all -- preserved here rather than in the client.
            active=data.get("active", True),
        )


@dataclass
class GetOperationsRequest:
    """GET endpoints.OPERATIONS -- list the operations the user is a member of."""

    skip_archived: bool = False

    def to_form_data(self):
        return {"skip_archived": str(self.skip_archived)}

    @classmethod
    def from_args_and_form(cls, args, form):
        """Mirrors the route's ``request.args.get(x, request.form.get(x, default))``
        fallback chain -- request_get() puts its payload in the request body,
        so request.args is normally empty, but the handler has always checked
        both.
        """
        return cls(skip_archived=args.get("skip_archived", form.get("skip_archived", "False")) == "True")


@dataclass
class GetOperationsResponse:
    """Response body for GET endpoints.OPERATIONS.

    The server passes FileManager.list_operations' dicts through; from_text()
    returns OperationInfo entries.
    """

    operations: List[Union[OperationInfo, dict]] = field(default_factory=list)

    def to_text(self):
        return json.dumps({"operations": [_record_dict(op) for op in self.operations]})

    @classmethod
    def from_text(cls, text):
        """Returns None if the token was rejected (see AUTH_FAILED_TEXT)."""
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(operations=[OperationInfo.from_dict(op) for op in json.loads(text)["operations"]])


@dataclass
class GetOperationByIdRequest:
    """GET endpoints.GET_OPERATION_BY_ID -- fetch one operation's FTML content."""

    op_id: int

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        # int(None) raises TypeError here, same as the route's previous bare
        # request.args/request.form reads -- a missing op_id was never
        # validated any more gracefully than that.
        return cls(op_id=int(args.get("op_id", form.get("op_id", None))))


@dataclass
class GetOperationByIdResponse:
    """Response body for GET endpoints.GET_OPERATION_BY_ID.

    The route returns bare "False" (see AUTH_FAILED_TEXT) both when the token
    is rejected AND when fm.get_file() itself returns False (operation not
    found / user not a member) -- the two cases are indistinguishable on the
    wire today. from_text() preserves that ambiguity rather than inventing a
    distinction the server doesn't actually make.
    """

    content: str

    def to_text(self):
        return json.dumps({"content": self.content})

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(content=json.loads(text)["content"])


@dataclass
class DeleteOperationRequest:
    """POST endpoints.DELETE_OPERATION."""

    op_id: int

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_form(cls, form):
        # int(...) on a missing op_id defaults to 0 -- matches the route's
        # previous request.form.get('op_id', 0).
        return cls(op_id=int(form.get("op_id", 0)))


@dataclass
class DeleteOperationResponse:
    """Response body for POST endpoints.DELETE_OPERATION.

    The route serves this via flask.jsonify (Content-Type: application/json),
    unlike most other routes migrated so far -- to_dict() lets the handler
    keep doing that (jsonify(response.to_dict())) instead of silently
    downgrading the response's Content-Type to text/html.
    """

    success: bool
    message: str

    def to_dict(self):
        return {"success": self.success, "message": self.message}

    def to_text(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], message=data["message"])


@dataclass
class UpdateOperationRequest:
    """POST endpoints.UPDATE_OPERATION -- change one attribute of an
    operation (path/description/category/active), one call per attribute.
    """

    op_id: int
    attribute: str
    value: str

    def to_form_data(self):
        return {"op_id": self.op_id, "attribute": self.attribute, "value": self.value}

    @classmethod
    def from_form(cls, form):
        # int(None) raises TypeError on a missing op_id, and form["attribute"]/
        # form["value"] raise KeyError -- matches the route's previous bare
        # request.form reads exactly.
        return cls(op_id=int(form.get("op_id", None)), attribute=form["attribute"], value=form["value"])


@dataclass
class UpdateOperationResponse:
    """Response body for POST endpoints.UPDATE_OPERATION: plain-text "True"/"False"."""

    success: bool

    def to_text(self):
        return str(self.success)

    @classmethod
    def from_text(cls, text):
        return cls(success=(text == "True"))


@dataclass
class GetCreatorOfOperationRequest:
    """GET endpoints.GET_CREATOR_OF_OPERATION.

    Unlike the other op_id-taking routes, this one never casts op_id to int
    before querying the DB (SQLite tolerates the string; preserved as-is
    rather than "fixed" here).
    """

    op_id: object

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(op_id=args.get("op_id", form.get("op_id", None)))


@dataclass
class GetCreatorOfOperationResponse:
    """Response body for GET endpoints.GET_CREATOR_OF_OPERATION.

    HTTP 200 + {"success": True, "username": ...} on success, HTTP 403 +
    {"success": False, "message": ...} if the caller isn't a member of the
    operation. mslib.msui.mscolab.view_description only ever sees the success
    shape in practice: request_get() raises MSColabConnectionError itself on
    any non-200 status, before the body is ever parsed.
    """

    success: bool
    username: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self):
        if self.success:
            return {"success": True, "username": self.username}
        return {"success": False, "message": self.message}

    @classmethod
    def from_text(cls, text):
        data = json.loads(text)
        return cls(success=data["success"], username=data.get("username"), message=data.get("message"))


@dataclass
class DeleteBulkPermissionsRequest:
    """POST endpoints.DELETE_BULK_PERMISSIONS -- revoke one or more users'
    permissions on an operation in one call (also used to "leave" an
    operation, by passing just the caller's own user id).
    """

    op_id: int
    user_ids: List[int]

    def to_form_data(self):
        return {"op_id": self.op_id, "selected_userids": json.dumps(self.user_ids)}

    @classmethod
    def from_form(cls, form):
        return cls(op_id=int(form.get("op_id")), user_ids=json.loads(form.get("selected_userids", "[]")))


@dataclass
class DeleteBulkPermissionsResponse:
    """Response body for POST endpoints.DELETE_BULK_PERMISSIONS."""

    success: bool
    message: str

    def to_dict(self):
        return {"success": self.success, "message": self.message}

    def to_text(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], message=data["message"])


@dataclass
class UserInfo:
    """The logged-in user, as returned by GET endpoints.USER and (with the
    same three fields) embedded in the response of POST "token" (login,
    not yet migrated).
    """

    id: int  # noqa: A003
    username: str
    fullname: str

    def to_dict(self):
        return {"id": self.id, "username": self.username, "fullname": self.fullname}

    @classmethod
    def from_dict(cls, data):
        return cls(id=data["id"], username=data["username"], fullname=data["fullname"])


@dataclass
class GetUserResponse:
    """Response body for GET endpoints.USER."""

    user: UserInfo

    def to_text(self):
        return json.dumps({"user": self.user.to_dict()})

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(user=UserInfo.from_dict(json.loads(text)["user"]))


@dataclass
class LoginRequest:
    """POST endpoints.TOKEN -- log in (email+password), or complete an IDP
    login by posting the IDP-issued token as the "password".
    """

    email: str
    password: str

    def to_form_data(self):
        return {"email": self.email, "password": self.password}

    @classmethod
    def from_form(cls, form):
        return cls(email=form["email"], password=form["password"])


@dataclass
class LoginResponse:
    """Response body for POST endpoints.TOKEN."""

    token: str
    user: UserInfo

    def to_text(self):
        return json.dumps({"token": self.token, "user": self.user.to_dict()})

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(token=data["token"], user=UserInfo.from_dict(data["user"]))


@dataclass
class UploadProfileImageRequest:
    """POST endpoints.UPLOAD_PROFILE_IMAGE (multipart, plus an "image" file
    field the client attaches separately -- not part of this dataclass).

    user_id is sent by the client but ignored server-side (the route uses
    g.user.id from the auth token instead) -- preserved as-is here, since
    it's still part of the actual wire payload today.
    """

    user_id: int

    def to_form_data(self):
        return {"user_id": self.user_id}


@dataclass
class FetchProfileImageRequest:
    """GET endpoints.FETCH_PROFILE_IMAGE."""

    user_id: int
    op_id: Optional[int] = None

    def to_form_data(self):
        data = {"user_id": self.user_id}
        if self.op_id is not None:
            data["op_id"] = self.op_id
        return data

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(user_id=form["user_id"], op_id=args.get("op_id", form.get("op_id", None)))


@dataclass
class ProfileImageMessageResponse:
    """The {"message": str} JSON body used by upload_profile_image (every
    status code) and fetch_profile_image's HTTP 404 failure path. Neither
    client call site parses this today -- upload checks response.status_code
    and shows response.text raw on failure; fetch only ever reads
    response.content (raw image bytes) on success and otherwise relies on
    request_get() raising MSColabConnectionError for any non-200 status. This
    documents the shape the server actually sends, for whoever eventually
    wires up proper error display.
    """

    message: str

    def to_dict(self):
        return {"message": self.message}

    @classmethod
    def from_text(cls, text):
        return cls(message=json.loads(text)["message"])


@dataclass
class DeleteOwnAccountResponse:
    """Response body for POST endpoints.DELETE_OWN_ACCOUNT."""

    success: bool

    def to_dict(self):
        return {"success": self.success}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(success=json.loads(text)["success"])


@dataclass
class GetOperationUsersRequest:
    """GET endpoints.USERS_WITHOUT_PERMISSION / endpoints.USERS_WITH_PERMISSION
    -- identical request shape for both routes.
    """

    op_id: int

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(op_id=int(args.get("op_id", form.get("op_id", None))))


@dataclass
class GetOperationUsersResponse:
    """Response body for both endpoints.USERS_WITHOUT_PERMISSION and
    endpoints.USERS_WITH_PERMISSION -- identical shape for both routes.

    `users` is a list of plain [username, id] / [username, access_level, id]
    rows (not a list of dicts) -- that's the actual shape
    FileManager.fetch_users_{with,without}_permission returns, and what
    MSColabAdminWindow.populate_table() consumes directly by column index,
    so it's kept as-is rather than wrapped in a per-user dataclass.
    """

    success: bool
    users: Optional[list] = None
    message: Optional[str] = None

    def to_dict(self):
        if self.success:
            return {"success": True, "users": self.users}
        return {"success": False, "message": self.message}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], users=data.get("users"), message=data.get("message"))


@dataclass
class BulkPermissionsRequest:
    """POST endpoints.ADD_BULK_PERMISSIONS / endpoints.MODIFY_BULK_PERMISSIONS
    -- identical request shape for both routes.
    """

    op_id: int
    user_ids: List[int]
    access_level: str

    def to_form_data(self):
        return {
            "op_id": self.op_id,
            "selected_userids": json.dumps(self.user_ids),
            "selected_access_level": self.access_level,
        }

    @classmethod
    def from_form(cls, form):
        return cls(
            op_id=int(form.get("op_id")),
            user_ids=json.loads(form.get("selected_userids", "[]")),
            access_level=form.get("selected_access_level"),
        )


@dataclass
class BulkPermissionsResponse:
    """Response body for both endpoints.ADD_BULK_PERMISSIONS and
    endpoints.MODIFY_BULK_PERMISSIONS -- identical shape for both routes.
    """

    success: bool
    message: str

    def to_dict(self):
        return {"success": self.success, "message": self.message}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], message=data["message"])


@dataclass
class ImportPermissionsRequest:
    """POST endpoints.IMPORT_PERMISSIONS -- copy all permissions from one
    operation onto another.
    """

    current_op_id: int
    import_op_id: int

    def to_form_data(self):
        return {"current_op_id": self.current_op_id, "import_op_id": self.import_op_id}

    @classmethod
    def from_form(cls, form):
        return cls(
            current_op_id=int(form.get("current_op_id")),
            import_op_id=int(form.get("import_op_id")),
        )


@dataclass
class ImportPermissionsResponse:
    """Response body for POST endpoints.IMPORT_PERMISSIONS.

    message is only ever present on failure -- the success path returns bare
    {"success": True}, with no message field at all.
    """

    success: bool
    message: Optional[str] = None

    def to_dict(self):
        if self.success:
            return {"success": True}
        return {"success": False, "message": self.message}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], message=data.get("message"))


@dataclass
class AuthorizedUserInfo:
    """One entry of GetAuthorizedUsersResponse.users -- mirrors the dict
    FileManager.get_authorized_users builds per row (a different shape than
    OperationInfo/GetOperationUsersResponse's plain list rows).
    """

    username: str
    access_level: str
    id: int  # noqa: A003

    def to_dict(self):
        return {"username": self.username, "access_level": self.access_level, "id": self.id}

    @classmethod
    def from_dict(cls, data):
        return cls(username=data["username"], access_level=data["access_level"], id=data["id"])


@dataclass
class GetAuthorizedUsersRequest:
    """GET endpoints.AUTHORIZED_USERS -- everyone with any permission on the
    operation (as opposed to endpoints.USERS_WITH_PERMISSION, which is
    admin-only and excludes the caller and the creator).
    """

    op_id: int

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(op_id=int(args.get("op_id", form.get("op_id", None))))


@dataclass
class GetAuthorizedUsersResponse:
    """Response body for GET endpoints.AUTHORIZED_USERS.

    The server passes FileManager.get_authorized_users' dicts through;
    from_text() returns AuthorizedUserInfo entries.
    """

    users: List[Union[AuthorizedUserInfo, dict]]

    def to_text(self):
        return json.dumps({"users": [_record_dict(u) for u in self.users]})

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(users=[AuthorizedUserInfo.from_dict(u) for u in json.loads(text)["users"]])


@dataclass
class GetActiveUsersRequest:
    """GET endpoints.ACTIVE_USERS."""

    op_id: int

    def to_form_data(self):
        return {"op_id": self.op_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(op_id=int(args.get("op_id", form.get("op_id", None))))


@dataclass
class GetActiveUsersResponse:
    """Response body for GET endpoints.ACTIVE_USERS -- user ids currently
    connected to the operation's socket.io room.
    """

    active_users: List[int]

    def to_dict(self):
        return {"active_users": self.active_users}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(active_users=json.loads(text)["active_users"])


@dataclass
class ChangeInfo:
    """One entry of GetAllChangesResponse.changes -- mirrors the dict
    FileManager.get_all_changes builds per row.
    """

    id: int  # noqa: A003
    comment: Optional[str]
    version_name: Optional[str]
    username: str
    created_at: str

    def to_dict(self):
        return {
            "id": self.id,
            "comment": self.comment,
            "version_name": self.version_name,
            "username": self.username,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            comment=data["comment"],
            version_name=data["version_name"],
            username=data["username"],
            created_at=data["created_at"],
        )


@dataclass
class GetAllChangesRequest:
    """GET endpoints.GET_ALL_CHANGES.

    named_version is sent as a real URL query parameter (?named_version=...);
    op_id (and token) go in the request body via requests' data= -- two
    separate wire channels, preserved as-is rather than merged into one,
    since that's the actual client behavior today.
    """

    op_id: int
    named_version: bool = False

    def to_form_data(self):
        return {"op_id": self.op_id}

    def to_query_string(self):
        return urlencode({"named_version": self.named_version})

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(
            op_id=int(args.get("op_id", form.get("op_id", None))),
            named_version=args.get("named_version") == "True",
        )


@dataclass
class GetAllChangesResponse:
    """Response body for GET endpoints.GET_ALL_CHANGES.

    A caller who isn't a member of the operation gets success=False with an
    empty changes list.
    """

    success: bool
    changes: List[Union[ChangeInfo, dict]]

    def to_dict(self):
        return {"success": self.success, "changes": [_record_dict(c) for c in self.changes]}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], changes=[ChangeInfo.from_dict(c) for c in data["changes"]])


@dataclass
class GetChangeContentRequest:
    """GET endpoints.GET_CHANGE_CONTENT."""

    ch_id: int

    def to_form_data(self):
        return {"ch_id": self.ch_id}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(ch_id=int(args.get("ch_id", form.get("ch_id", 0))))


@dataclass
class GetChangeContentResponse:
    """Response body for GET endpoints.GET_CHANGE_CONTENT.

    Unlike get_operation_by_id (a bare json.dumps string), this route uses
    flask.jsonify on the success path -- to_dict() lets the handler keep
    doing that instead of silently changing the response's Content-Type.
    """

    content: str

    def to_dict(self):
        return {"content": self.content}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        return cls(content=json.loads(text)["content"])


@dataclass
class SetVersionNameRequest:
    """POST endpoints.SET_VERSION_NAME.

    version_name is sent as None to clear a version name
    (MSColabVersionHistory.handle_delete_version_name) -- requests drops
    None-valued form fields, matching the route's own
    request.form.get('version_name', None) default, so to_form_data() omits
    it explicitly here too rather than relying on that requests behavior.
    """

    op_id: int
    ch_id: int
    version_name: Optional[str] = None

    def to_form_data(self):
        data = {"op_id": self.op_id, "ch_id": self.ch_id}
        if self.version_name is not None:
            data["version_name"] = self.version_name
        return data

    @classmethod
    def from_form(cls, form):
        return cls(
            op_id=int(form.get("op_id", 0)),
            ch_id=int(form.get("ch_id", 0)),
            version_name=form.get("version_name", None),
        )


@dataclass
class SetVersionNameResponse:
    """Response body for POST endpoints.SET_VERSION_NAME."""

    success: bool
    message: str

    def to_dict(self):
        return {"success": self.success, "message": self.message}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], message=data["message"])


@dataclass
class UndoChangesRequest:
    """POST endpoints.UNDO_CHANGES."""

    ch_id: int

    def to_form_data(self):
        return {"ch_id": self.ch_id}

    @classmethod
    def from_form(cls, form):
        return cls(ch_id=int(form.get("ch_id", -1)))


@dataclass
class UndoChangesResponse:
    """Response body for POST endpoints.UNDO_CHANGES: plain-text "True"/"False"."""

    success: bool

    def to_text(self):
        return str(self.success)

    @classmethod
    def from_text(cls, text):
        return cls(success=(text == "True"))


@dataclass
class StatusResponse:
    """Response body for GET endpoints.STATUS.

    message is present on the wire but never consumed by the client. Unlike
    every other response so far, from_text() has to tolerate a body that
    isn't valid JSON at all: mscolab_connect_dialog.py's connect_handler
    reads use_saml2 and direct_login as two independent
    try/except(JSONDecodeError, KeyError) lookups, defaulting to False and
    True respectively on failure -- preserved here as the same two
    independent per-field defaults, applied whether the text fails to parse
    at all or parses but is missing a key.
    """

    message: str
    use_saml2: bool
    direct_login: bool

    def to_dict(self):
        return {"message": self.message, "use_saml2": self.use_saml2, "direct_login": self.direct_login}

    @classmethod
    def from_text(cls, text):
        try:
            data = json.loads(text)
        except json.decoder.JSONDecodeError:
            data = {}
        return cls(
            message=data.get("message", ""),
            use_saml2=data.get("use_saml2", False),
            direct_login=data.get("direct_login", True),
        )


@dataclass
class RegisterRequest:
    """POST endpoints.REGISTER -- create a new mscolab user account."""

    email: str
    password: str
    username: str
    fullname: str

    def to_form_data(self):
        return {"email": self.email, "password": self.password, "username": self.username, "fullname": self.fullname}

    @classmethod
    def from_form(cls, form):
        return cls(
            email=form["email"], password=form["password"], username=form["username"], fullname=form["fullname"])


@dataclass
class RegisterResponse:
    """Response body for POST endpoints.REGISTER.

    message is present on the route's validation-failure paths (empty
    email/username, invalid email, duplicate email/username) but absent on
    its final {"success": result} path (FileManager.modify_user's own
    outcome, win or lose) -- modeled as optional rather than forcing a
    default that was never really on the wire. mscolab_connect_dialog.py's
    new_user_handler never actually parses this body anyway (it only
    branches on the HTTP status code: 204/201/other).
    """

    success: bool
    message: Optional[str] = None

    def to_dict(self):
        if self.message is not None:
            return {"success": self.success, "message": self.message}
        return {"success": self.success}

    @classmethod
    def from_text(cls, text):
        data = json.loads(text)
        return cls(success=data["success"], message=data.get("message"))


@dataclass
class IdpLoginAuthRequest:
    """POST endpoints.IDP_LOGIN_AUTH -- submit the SAML-issued token to
    complete an IDP login.

    Unlike every other route migrated so far, the client sends this as a
    real JSON body (`requests.post(url, json=...)`), not form-encoded data,
    and the server reads it via `request.get_json()`, not `request.form` --
    so this is `to_json_data()`/`from_json_data()`, not
    `to_form_data()`/`from_form()`.
    """

    token: str

    def to_json_data(self):
        return {"token": self.token}

    @classmethod
    def from_json_data(cls, data):
        return cls(token=data.get("token"))


@dataclass
class IdpUserInfo:
    """User info embedded in IdpLoginAuthResponse -- a different shape than
    UserInfo (username/id/emailid here, vs. username/id/fullname there; no
    route shares this exact shape with any other migrated so far).
    """

    username: str
    id: int  # noqa: A003
    emailid: str

    def to_dict(self):
        return {"username": self.username, "id": self.id, "emailid": self.emailid}

    @classmethod
    def from_dict(cls, data):
        return cls(username=data["username"], id=data["id"], emailid=data["emailid"])


@dataclass
class IdpLoginAuthResponse:
    """Response body for POST endpoints.IDP_LOGIN_AUTH.

    The success path returns via a bare json.dumps (text/html Content-Type,
    same pattern as create_operation/get_operation_by_id) with
    {"success": True, "token": ..., "user": {...}}. Every failure path
    (invalid/expired token, no matching user, or a malformed request
    raising TypeError) returns via flask.jsonify (application/json) with
    just {"success": False} and HTTP 401 -- to_dict() lets the handler keep
    using jsonify() for that path without silently changing its
    Content-Type, mirroring DeleteOperationResponse's to_dict()/to_text()
    split.
    """

    success: bool
    token: Optional[str] = None
    user: Optional[IdpUserInfo] = None

    def to_text(self):
        return json.dumps({"success": self.success, "token": self.token, "user": self.user.to_dict()})

    def to_dict(self):
        return {"success": self.success}

    @classmethod
    def from_text(cls, text):
        data = json.loads(text)
        user = IdpUserInfo.from_dict(data["user"]) if "user" in data else None
        return cls(success=data["success"], token=data.get("token"), user=user)


@dataclass
class ChatMessageInfo:
    """One message or reply, as returned by ChatManager.get_messages() and
    embedded in the mscolab.api.events.SocketEvents.CHAT_MESSAGE_CLIENT
    real-time event (that socket payload is a separate, not-yet-typed
    contract -- see restructuring notes -- this dataclass only models the
    REST side, endpoints.MESSAGES).

    A reply's own `replies` is always an empty list (replies are one level
    deep only in this chat feature) -- not special-cased here, this just
    models the actual recursive shape as FileManager/ChatManager build it.
    """

    id: int  # noqa: A003
    u_id: int
    username: str
    text: str
    message_type: int
    reply_id: Optional[int]
    replies: List["ChatMessageInfo"]
    time: str

    def to_dict(self):
        return {
            "id": self.id,
            "u_id": self.u_id,
            "username": self.username,
            "text": self.text,
            "message_type": self.message_type,
            "reply_id": self.reply_id,
            "replies": [r.to_dict() for r in self.replies],
            "time": self.time,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            u_id=data["u_id"],
            username=data["username"],
            text=data["text"],
            message_type=data["message_type"],
            reply_id=data["reply_id"],
            replies=[cls.from_dict(r) for r in data["replies"]],
            time=data["time"],
        )


@dataclass
class GetMessagesRequest:
    """GET endpoints.MESSAGES.

    op_id is never cast to int server-side (same as
    GetCreatorOfOperationRequest.op_id) -- preserved, not "fixed".
    """

    op_id: object
    timestamp: str = "1970-01-01T00:00:00+00:00"

    def to_form_data(self):
        return {"op_id": self.op_id, "timestamp": self.timestamp}

    @classmethod
    def from_args_and_form(cls, args, form):
        return cls(
            op_id=args.get("op_id", form.get("op_id", None)),
            timestamp=args.get("timestamp", form.get("timestamp", "1970-01-01T00:00:00+00:00")),
        )


@dataclass
class GetMessagesResponse:
    """Response body for GET endpoints.MESSAGES.

    The route's own "not a member" check returns bare "False" (not via
    verify_user, but the same wire value) -- from_text() treats it the same
    way as the shared AUTH_FAILED_TEXT sentinel, since the client can't
    (and doesn't) distinguish the two cases either.

    The server passes ChatManager.get_messages' dicts through; from_text()
    returns ChatMessageInfo entries.
    """

    messages: List[Union[ChatMessageInfo, dict]]

    def to_dict(self):
        return {"messages": [_record_dict(m) for m in self.messages]}

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(messages=[ChatMessageInfo.from_dict(m) for m in data["messages"]])


@dataclass
class MessageAttachmentRequest:
    """POST endpoints.MESSAGE_ATTACHMENT (multipart, plus a "file" field the
    client attaches separately -- not part of this dataclass).

    op_id is never cast to int server-side (same pattern as
    GetCreatorOfOperationRequest.op_id) -- preserved, not "fixed".
    """

    op_id: object
    message_type: Optional[int]

    def to_form_data(self):
        return {"op_id": self.op_id, "message_type": self.message_type}

    @classmethod
    def from_form(cls, form):
        # a missing message_type must not fail before the route's membership check
        message_type = form.get("message_type")
        return cls(op_id=form.get("op_id", None),
                   message_type=int(message_type) if message_type is not None else None)


@dataclass
class MessageAttachmentResponse:
    """Response body for POST endpoints.MESSAGE_ATTACHMENT.

    Bare "False" (the shared AUTH_FAILED_TEXT sentinel value, though not
    from @verify_user here) covers two different server-side reasons --
    the caller isn't a member (or is a view-only member), or
    FileManager.upload_file() itself returned None -- indistinguishable on
    the wire, same as elsewhere. The {"success": False, "message": ...}
    shape is also modeled (the route has a branch that builds it), though
    it looks unreachable in practice: request.files['file'] either returns
    a FileStorage or raises before that branch's `if file is not None`
    check could ever see None -- not fixed here, just not asserted as dead
    with full confidence either.

    mscolab_chat.py's send_message() never actually parses any of this
    (it only catches requests.exceptions.ConnectionError, for "file too
    large"); modeled for whoever eventually wires up proper feedback.
    """

    success: bool
    path: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self):
        data = {"success": self.success}
        if self.path is not None:
            data["path"] = self.path
        if self.message is not None:
            data["message"] = self.message
        return data

    @classmethod
    def from_text(cls, text):
        if text == AUTH_FAILED_TEXT:
            return None
        data = json.loads(text)
        return cls(success=data["success"], path=data.get("path"), message=data.get("message"))
