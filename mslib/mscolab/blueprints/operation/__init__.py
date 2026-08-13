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

OPERATION_BP = Blueprint('operation', __name__)


@OPERATION_BP.route('/create_operation', methods=["POST"])
@verify_user
def create_operation():
    fm = current_app.extensions['fm']
    path = request.form['path']
    content = request.form.get('content', None)
    description = request.form.get('description', None)
    category = request.form.get('category', "default")
    active = (request.form.get('active', "True") == "True")
    last_used = datetime.datetime.now(tz=datetime.timezone.utc)
    user = g.user
    r = str(fm.create_operation(path, description, user, last_used, content=content, category=category, active=active))
    if r == "True":
        sockio = current_app.extensions['sockio']
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return r


@OPERATION_BP.route('/get_operation_by_id', methods=['GET'])
@verify_user
def get_operation_by_id():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    user = g.user
    result = fm.get_file(int(op_id), user)
    if result is False:
        return "False"
    return json.dumps({"content": result})


@OPERATION_BP.route('/get_all_changes', methods=['GET'])
@verify_user
def get_all_changes():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    named_version = request.args.get('named_version') == "True"
    user = g.user
    result = fm.get_all_changes(int(op_id), user, named_version)
    if result is False:
        jsonify({"success": False, "message": "Some error occurred!"})
    return jsonify({"success": True, "changes": result})


@OPERATION_BP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    fm = current_app.extensions['fm']
    ch_id = int(request.args.get('ch_id', request.form.get('ch_id', 0)))
    user = g.user
    result = fm.get_change_content(ch_id, user)
    if result is False:
        return "False"
    return jsonify({"content": result})


@OPERATION_BP.route('/set_version_name', methods=['POST'])
@verify_user
def set_version_name():
    fm = current_app.extensions['fm']
    ch_id = int(request.form.get('ch_id', 0))
    op_id = int(request.form.get('op_id', 0))
    version_name = request.form.get('version_name', None)
    u_id = g.user.id
    success = fm.set_version_name(ch_id, op_id, u_id, version_name)
    if success is False:
        return jsonify({"success": False, "message": "Some error occurred!"})

    return jsonify({"success": True, "message": "Successfully set version name"})


@OPERATION_BP.route('/authorized_users', methods=['GET'])
@verify_user
def authorized_users():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    return json.dumps({"users": fm.get_authorized_users(int(op_id))})


@OPERATION_BP.route('/active_users', methods=["GET"])
@verify_user
def active_users():
    sockio = current_app.extensions['sockio']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    return jsonify(active_users=list(sockio.sm.active_users_per_operation[int(op_id)]))


@OPERATION_BP.route('/operations', methods=['GET'])
@verify_user
def get_operations():
    fm = current_app.extensions['fm']
    skip_archived = (request.args.get('skip_archived', request.form.get('skip_archived', "False")) == "True")
    user = g.user
    return json.dumps({"operations": fm.list_operations(user, skip_archived=skip_archived)})


@OPERATION_BP.route('/delete_operation', methods=["POST"])
@verify_user
def delete_operation():
    fm = current_app.extensions['fm']
    op_id = int(request.form.get('op_id', 0))
    user = g.user
    success = fm.delete_operation(op_id, user)
    if success is False:
        return jsonify({"success": False, "message": "You don't have access for this operation!"})
    sockio = current_app.extensions['sockio']
    sockio.sm.emit_operation_delete(op_id)
    return jsonify({"success": True, "message": "Operation was successfully deleted!"})


@OPERATION_BP.route('/update_operation', methods=['POST'])
@verify_user
def update_operation():
    fm = current_app.extensions['fm']
    op_id = request.form.get('op_id', None)
    attribute = request.form['attribute']
    value = request.form['value']
    user = g.user
    r = fm.update_operation(int(op_id), attribute, value, user)
    if r is True:
        sockio = current_app.extensions['sockio']
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return str(r)


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
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo_changes(ch_id, user)
    # get op_id from change
    ch = Change.query.filter_by(id=ch_id).first()
    if result is True:
        sockio = current_app.extensions['sockio']
        sockio.sm.emit_file_change(ch.op_id)
    return str(result)


@OPERATION_BP.route("/creator_of_operation", methods=["GET"])
@verify_user
def get_creator_of_operation():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    creator_name = fm.fetch_operation_creator(op_id, u_id)
    if creator_name is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403
    return jsonify({"success": True, "username": creator_name}), 200


@OPERATION_BP.route("/users_without_permission", methods=["GET"])
@verify_user
def get_users_without_permission():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    users = fm.fetch_users_without_permission(int(op_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@OPERATION_BP.route("/users_with_permission", methods=["GET"])
@verify_user
def get_users_with_permission():
    fm = current_app.extensions['fm']
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    users = fm.fetch_users_with_permission(int(op_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@OPERATION_BP.route("/add_bulk_permissions", methods=["POST"])
@verify_user
def add_bulk_permissions():
    fm = current_app.extensions['fm']
    op_id = int(request.form.get('op_id'))
    new_u_ids = json.loads(request.form.get('selected_userids', "[]"))
    access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.add_bulk_permission(op_id, user, new_u_ids, access_level)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in new_u_ids:
            sockio.sm.emit_new_permission(u_id, op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "Users successfully added!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@OPERATION_BP.route("/modify_bulk_permissions", methods=["POST"])
@verify_user
def modify_bulk_permissions():
    fm = current_app.extensions['fm']
    op_id = int(request.form.get('op_id'))
    u_ids = json.loads(request.form.get('selected_userids', "[]"))
    new_access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.modify_bulk_permission(op_id, user, u_ids, new_access_level)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in u_ids:
            sockio.sm.emit_update_permission(u_id, op_id, access_level=new_access_level)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "User permissions successfully updated!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@OPERATION_BP.route("/delete_bulk_permissions", methods=["POST"])
@verify_user
def delete_bulk_permissions():
    fm = current_app.extensions['fm']
    op_id = int(request.form.get('op_id'))
    u_ids = json.loads(request.form.get('selected_userids', "[]"))
    user = g.user
    success = fm.delete_bulk_permission(op_id, user, u_ids)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in u_ids:
            sockio.sm.remove_active_user_id_from_specific_operation(u_id, op_id)
            sockio.sm.emit_revoke_permission(u_id, op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "User permissions successfully deleted!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@OPERATION_BP.route('/import_permissions', methods=['POST'])
@verify_user
def import_permissions():
    fm = current_app.extensions['fm']
    import_op_id = int(request.form.get('import_op_id'))
    current_op_id = int(request.form.get('current_op_id'))
    user = g.user
    success, users, message = fm.import_permissions(import_op_id, current_op_id, user.id)
    if success:
        sockio = current_app.extensions['sockio']
        for u_id in users["add_users"]:
            sockio.sm.emit_new_permission(u_id, current_op_id)
        for u_id in users["modify_users"]:
            # changes navigation for viewer/collaborator
            sockio.sm.emit_update_permission(u_id, current_op_id)
        for u_id in users["delete_users"]:
            # invalidate waypoint table, title of windows
            sockio.sm.emit_revoke_permission(u_id, current_op_id)

        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)

        sockio.sm.emit_operation_permissions_updated(user.id, current_op_id)
        return jsonify({"success": True})

    return jsonify({"success": False,
                    "message": message})
