# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    User Blueprint for server for mscolab module

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

import json
from pathlib import Path

from flask import Blueprint, g, request, jsonify, send_from_directory, current_app

from mslib.mscolab.auth import verify_user

USER_BP = Blueprint('user', __name__)


@USER_BP.route('/user', methods=["GET"])
@verify_user
def get_user():
    return json.dumps({'user': {'id': g.user.id, 'username': g.user.username, 'fullname': g.user.fullname}})


@USER_BP.route('/upload_profile_image', methods=["POST"])
@verify_user
def upload_profile_image():
    user_id = g.user.id
    file = request.files['image']
    if not file:
        return jsonify({'message': 'No file provided or invalid file type'}), 400
    if not file.mimetype.startswith('image/'):
        return jsonify({'message': 'Invalid file type'}), 400
    if file.content_length > current_app.config['MAX_UPLOAD_SIZE']:
        return jsonify({'message': 'File too large'}), 413
    fm = current_app.extensions['fm']
    success, message = fm.save_user_profile_image(user_id, file)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'message': message}), 400


@USER_BP.route('/fetch_profile_image', methods=["GET"])
@verify_user
def fetch_profile_image():
    fm = current_app.extensions['fm']
    user_id = request.form['user_id']
    op_id = request.args.get("op_id", request.form.get("op_id", None))
    success, filename = fm.get_user_profile_image(user_id, op_id, g.user.id)
    if success:
        base_path = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(Path(base_path), filename)
    else:
        return jsonify({'message': 'User or profile image not found'}), 404


@USER_BP.route("/delete_own_account", methods=["POST"])
@verify_user
def delete_own_account():
    """
    delete own account
    """
    fm = current_app.extensions['fm']
    user = g.user
    result = fm.modify_user(user, action="delete")
    return jsonify({"success": result}), 200
