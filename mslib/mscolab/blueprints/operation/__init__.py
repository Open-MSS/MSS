# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.operation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Operation Blueprint for server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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

import datetime
import json

from flask import Blueprint, request, g, jsonify, current_app

from mslib.mscolab.auth import verify_user
from mslib.mscolab.models import Change
from mslib.mscolab.api.schemas import (
    AuthorizedUserInfo,
    BulkPermissionsRequest,
    BulkPermissionsResponse,
    CreateOperationRequest,
    CreateOperationResponse,
    DeleteBulkPermissionsRequest,
    DeleteBulkPermissionsResponse,
    DeleteOperationRequest,
    DeleteOperationResponse,
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
    GetOperationByIdRequest,
    GetOperationByIdResponse,
    GetOperationsRequest,
    GetOperationsResponse,
    GetOperationUsersRequest,
    GetOperationUsersResponse,
    ImportPermissionsRequest,
    ImportPermissionsResponse,
    OperationInfo,
    SetVersionNameRequest,
    SetVersionNameResponse,
    UndoChangesRequest,
    UndoChangesResponse,
    UpdateOperationRequest,
    UpdateOperationResponse,
)

OPERATION_BP = Blueprint('operation', __name__)


@OPERATION_BP.route('/create_operation', methods=["POST"])
@verify_user
def create_operation():
    fm = current_app.extensions['fm']
    req = CreateOperationRequest.from_form(request.form)
    last_used = datetime.datetime.now(tz=datetime.timezone.utc)
    user = g.user
    success = fm.create_operation(
        req.path, req.description, user, last_used, content=req.content, category=req.category, active=req.active)
    response = CreateOperationResponse(success=success)
    if response.success:
        sockio = current_app.extensions['sockio']
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return response.to_text()


@OPERATION_BP.route('/get_operation_by_id', methods=['GET'])
@verify_user
def get_operation_by_id():
    fm = current_app.extensions['fm']
    req = GetOperationByIdRequest.from_args_and_form(request.args, request.form)
    user = g.user
    result = fm.get_file(req.op_id, user)
    if result is False:
        return "False"
    return GetOperationByIdResponse(content=result).to_text()


@OPERATION_BP.route('/get_all_changes', methods=['GET'])
@verify_user
def get_all_changes():
    fm = current_app.extensions['fm']
    req = GetAllChangesRequest.from_args_and_form(request.args, request.form)
    user = g.user
    result = fm.get_all_changes(req.op_id, user, req.named_version)
    if result is False:
        # NOTE: pre-existing bug -- this response is never returned, so the
        # success path below always runs even when result is False. Preserved
        # as-is rather than silently fixed by this migration.
        jsonify(GetAllChangesResponse(success=False, changes=[]).to_dict())
    return jsonify(GetAllChangesResponse(success=True, changes=result).to_dict())


@OPERATION_BP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    fm = current_app.extensions['fm']
    req = GetChangeContentRequest.from_args_and_form(request.args, request.form)
    user = g.user
    result = fm.get_change_content(req.ch_id, user)
    if result is False:
        return "False"
    return jsonify(GetChangeContentResponse(content=result).to_dict())


@OPERATION_BP.route('/set_version_name', methods=['POST'])
@verify_user
def set_version_name():
    fm = current_app.extensions['fm']
    req = SetVersionNameRequest.from_form(request.form)
    u_id = g.user.id
    success = fm.set_version_name(req.ch_id, req.op_id, u_id, req.version_name)
    if success is False:
        return jsonify(SetVersionNameResponse(success=False, message="Some error occurred!").to_dict())

    return jsonify(SetVersionNameResponse(success=True, message="Successfully set version name").to_dict())


@OPERATION_BP.route('/authorized_users', methods=['GET'])
@verify_user
def authorized_users():
    fm = current_app.extensions['fm']
    req = GetAuthorizedUsersRequest.from_args_and_form(request.args, request.form)
    users = [AuthorizedUserInfo.from_dict(u) for u in fm.get_authorized_users(req.op_id)]
    return GetAuthorizedUsersResponse(users=users).to_text()


@OPERATION_BP.route('/active_users', methods=["GET"])
@verify_user
def active_users():
    sockio = current_app.extensions['sockio']
    req = GetActiveUsersRequest.from_args_and_form(request.args, request.form)
    response = GetActiveUsersResponse(active_users=list(sockio.sm.active_users_per_operation[req.op_id]))
    return jsonify(response.to_dict())


@OPERATION_BP.route('/operations', methods=['GET'])
@verify_user
def get_operations():
    fm = current_app.extensions['fm']
    req = GetOperationsRequest.from_args_and_form(request.args, request.form)
    user = g.user
    operations = [OperationInfo.from_dict(op) for op in fm.list_operations(user, skip_archived=req.skip_archived)]
    return GetOperationsResponse(operations=operations).to_text()


@OPERATION_BP.route('/delete_operation', methods=["POST"])
@verify_user
def delete_operation():
    fm = current_app.extensions['fm']
    req = DeleteOperationRequest.from_form(request.form)
    user = g.user
    success = fm.delete_operation(req.op_id, user)
    if success is False:
        return jsonify(DeleteOperationResponse(
            success=False, message="You don't have access for this operation!").to_dict())
    sockio = current_app.extensions['sockio']
    sockio.sm.emit_operation_delete(req.op_id)
    return jsonify(DeleteOperationResponse(success=True, message="Operation was successfully deleted!").to_dict())


@OPERATION_BP.route('/update_operation', methods=['POST'])
@verify_user
def update_operation():
    fm = current_app.extensions['fm']
    req = UpdateOperationRequest.from_form(request.form)
    user = g.user
    success = fm.update_operation(req.op_id, req.attribute, req.value, user)
    if success is True:
        sockio = current_app.extensions['sockio']
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return UpdateOperationResponse(success=success).to_text()


@OPERATION_BP.route('/operation_details', methods=["GET"])
@verify_user
def get_operation_details():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    user = g.user
    result = fm.get_operation_details(int(op_id), user)
    if result is False:
        return "False"
    return json.dumps(result)


@OPERATION_BP.route('/set_last_used', methods=["POST"])
@verify_user
def set_last_used():
    op_id = request.form.get('op_id', None)
    user = g.user
    days_ago = int(request.form.get('days', 0))
    if days_ago > 99999:
        days_ago = 99999
    elif days_ago < -99999:
        days_ago = -99999
    fm = current_app.extensions['fm']
    fm.update_operation(int(op_id), 'last_used',
                        datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=days_ago),
                        user)
    return jsonify({"success": True}), 200


@OPERATION_BP.route('/undo_changes', methods=["POST"])
@verify_user
def undo_changes():
    fm = current_app.extensions['fm']
    req = UndoChangesRequest.from_form(request.form)
    user = g.user
    result = fm.undo_changes(req.ch_id, user)
    # get op_id from change
    ch = Change.query.filter_by(id=req.ch_id).first()
    if result is True:
        sockio = current_app.extensions['sockio']
        sockio.sm.emit_file_change(ch.op_id)
    return UndoChangesResponse(success=result).to_text()


@OPERATION_BP.route("/creator_of_operation", methods=["GET"])
@verify_user
def get_creator_of_operation():
    fm = current_app.extensions['fm']
    req = GetCreatorOfOperationRequest.from_args_and_form(request.args, request.form)
    u_id = g.user.id
    creator_name = fm.fetch_operation_creator(req.op_id, u_id)
    if creator_name is False:
        response = GetCreatorOfOperationResponse(success=False, message="You don't have access to this data")
        return jsonify(response.to_dict()), 403
    response = GetCreatorOfOperationResponse(success=True, username=creator_name)
    return jsonify(response.to_dict()), 200


@OPERATION_BP.route("/users_without_permission", methods=["GET"])
@verify_user
def get_users_without_permission():
    fm = current_app.extensions['fm']
    req = GetOperationUsersRequest.from_args_and_form(request.args, request.form)
    u_id = g.user.id
    users = fm.fetch_users_without_permission(req.op_id, u_id)
    if users is False:
        response = GetOperationUsersResponse(success=False, message="You don't have access to this data")
        return jsonify(response.to_dict()), 403

    return jsonify(GetOperationUsersResponse(success=True, users=users).to_dict()), 200


@OPERATION_BP.route("/users_with_permission", methods=["GET"])
@verify_user
def get_users_with_permission():
    fm = current_app.extensions['fm']
    req = GetOperationUsersRequest.from_args_and_form(request.args, request.form)
    u_id = g.user.id
    users = fm.fetch_users_with_permission(req.op_id, u_id)
    if users is False:
        response = GetOperationUsersResponse(success=False, message="You don't have access to this data")
        return jsonify(response.to_dict()), 403

    return jsonify(GetOperationUsersResponse(success=True, users=users).to_dict()), 200


@OPERATION_BP.route("/add_bulk_permissions", methods=["POST"])
@verify_user
def add_bulk_permissions():
    fm = current_app.extensions['fm']
    req = BulkPermissionsRequest.from_form(request.form)
    user = g.user
    success = fm.add_bulk_permission(req.op_id, user, req.user_ids, req.access_level)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in req.user_ids:
            sockio.sm.emit_new_permission(u_id, req.op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, req.op_id)
        return jsonify(BulkPermissionsResponse(success=True, message="Users successfully added!").to_dict())

    return jsonify(
        BulkPermissionsResponse(success=False, message="Some error occurred. Please try again.").to_dict())


@OPERATION_BP.route("/modify_bulk_permissions", methods=["POST"])
@verify_user
def modify_bulk_permissions():
    fm = current_app.extensions['fm']
    req = BulkPermissionsRequest.from_form(request.form)
    user = g.user
    success = fm.modify_bulk_permission(req.op_id, user, req.user_ids, req.access_level)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in req.user_ids:
            sockio.sm.emit_update_permission(u_id, req.op_id, access_level=req.access_level)
        sockio.sm.emit_operation_permissions_updated(user.id, req.op_id)
        response = BulkPermissionsResponse(success=True, message="User permissions successfully updated!")
        return jsonify(response.to_dict())

    return jsonify(
        BulkPermissionsResponse(success=False, message="Some error occurred. Please try again.").to_dict())


@OPERATION_BP.route("/delete_bulk_permissions", methods=["POST"])
@verify_user
def delete_bulk_permissions():
    fm = current_app.extensions['fm']
    req = DeleteBulkPermissionsRequest.from_form(request.form)
    user = g.user
    success = fm.delete_bulk_permission(req.op_id, user, req.user_ids)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in req.user_ids:
            sockio.sm.remove_active_user_id_from_specific_operation(u_id, req.op_id)
            sockio.sm.emit_revoke_permission(u_id, req.op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, req.op_id)
        response = DeleteBulkPermissionsResponse(success=True, message="User permissions successfully deleted!")
        return jsonify(response.to_dict())

    response = DeleteBulkPermissionsResponse(success=False, message="Some error occurred. Please try again.")
    return jsonify(response.to_dict())


@OPERATION_BP.route('/import_permissions', methods=['POST'])
@verify_user
def import_permissions():
    fm = current_app.extensions['fm']
    req = ImportPermissionsRequest.from_form(request.form)
    user = g.user
    success, users, message = fm.import_permissions(req.import_op_id, req.current_op_id, user.id)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in users["add_users"]:
            sockio.sm.emit_new_permission(u_id, req.current_op_id)
        for u_id in users["modify_users"]:
            # changes navigation for viewer/collaborator
            sockio.sm.emit_update_permission(u_id, req.current_op_id)
        for u_id in users["delete_users"]:
            # invalidate waypoint table, title of windows
            sockio.sm.emit_revoke_permission(u_id, req.current_op_id)

        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)

        sockio.sm.emit_operation_permissions_updated(user.id, req.current_op_id)
        return jsonify(ImportPermissionsResponse(success=True).to_dict())

    return jsonify(ImportPermissionsResponse(success=False, message=message).to_dict())
