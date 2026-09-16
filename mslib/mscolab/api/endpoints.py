# -*- coding: utf-8 -*-
"""

    mslib.mscolab.api.endpoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Named registry of mscolab REST endpoint paths. The client
    (mslib/msui/mscolab.py) builds requests against these names instead of
    bare strings, so an endpoint rename is a single-point change instead of a
    grep across both sides of the client/server boundary.

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

# Only routes that have been migrated to typed schemas (see schemas.py) are
# listed here -- the rest of mscolab's ~50 routes are still referenced as
# bare strings on the client side until they are migrated too.
CREATE_OPERATION = "create_operation"
OPERATIONS = "operations"
GET_OPERATION_BY_ID = "get_operation_by_id"
DELETE_OPERATION = "delete_operation"
UPDATE_OPERATION = "update_operation"
GET_CREATOR_OF_OPERATION = "creator_of_operation"
DELETE_BULK_PERMISSIONS = "delete_bulk_permissions"
USER = "user"
TOKEN = "token"
UPLOAD_PROFILE_IMAGE = "upload_profile_image"
FETCH_PROFILE_IMAGE = "fetch_profile_image"
DELETE_OWN_ACCOUNT = "delete_own_account"
USERS_WITHOUT_PERMISSION = "users_without_permission"
USERS_WITH_PERMISSION = "users_with_permission"
ADD_BULK_PERMISSIONS = "add_bulk_permissions"
MODIFY_BULK_PERMISSIONS = "modify_bulk_permissions"
IMPORT_PERMISSIONS = "import_permissions"
AUTHORIZED_USERS = "authorized_users"
ACTIVE_USERS = "active_users"
GET_ALL_CHANGES = "get_all_changes"
GET_CHANGE_CONTENT = "get_change_content"
SET_VERSION_NAME = "set_version_name"
UNDO_CHANGES = "undo_changes"
STATUS = "status"
REGISTER = "register"
IDP_LOGIN_AUTH = "idp_login_auth"
MESSAGES = "messages"
MESSAGE_ATTACHMENT = "message_attachment"
