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

import io
from pathlib import Path

from PIL import Image
from flask import Blueprint, g, request, jsonify, send_from_directory, current_app

from mslib.mscolab.auth import verify_user
from mslib.mscolab.api import endpoints
from mslib.mscolab.api.schemas import (
    DeleteOwnAccountResponse,
    FetchProfileImageRequest,
    GetUserResponse,
    ProfileImageMessageResponse,
    UserInfo,
)

USER_BP = Blueprint('user', __name__)


@USER_BP.route(f"/{endpoints.USER}", methods=["GET"])
@verify_user
def get_user():
    user = UserInfo(id=g.user.id, username=g.user.username, fullname=g.user.fullname)
    return GetUserResponse(user=user).to_text()


@USER_BP.route(f"/{endpoints.UPLOAD_PROFILE_IMAGE}", methods=["POST"])
@verify_user
def upload_profile_image():
    user_id = g.user.id
    file = request.files['image']
    if not file:
        return jsonify(ProfileImageMessageResponse(message='No file provided or invalid file type').to_dict()), 400
    data = file.read()
    if len(data) > current_app.config['MAX_UPLOAD_SIZE']:
        return jsonify(ProfileImageMessageResponse(message='File too large').to_dict()), 413
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
    except Exception:
        return jsonify(ProfileImageMessageResponse(message='Invalid file type').to_dict()), 400
    file.seek(0)
    fm = current_app.extensions['fm']
    success, message = fm.save_user_profile_image(user_id, file)
    status_code = 200 if success else 400
    return jsonify(ProfileImageMessageResponse(message=message).to_dict()), status_code


@USER_BP.route(f"/{endpoints.FETCH_PROFILE_IMAGE}", methods=["GET"])
@verify_user
def fetch_profile_image():
    fm = current_app.extensions['fm']
    req = FetchProfileImageRequest.from_args_and_form(request.args, request.form)
    success, filename = fm.get_user_profile_image(req.user_id, req.op_id, g.user.id)
    if success:
        base_path = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(Path(base_path), filename)
    else:
        response = ProfileImageMessageResponse(message='User or profile image not found')
        return jsonify(response.to_dict()), 404


@USER_BP.route(f"/{endpoints.DELETE_OWN_ACCOUNT}", methods=["POST"])
@verify_user
def delete_own_account():
    """
    delete own account
    """
    fm = current_app.extensions['fm']
    user = g.user
    result = fm.modify_user(user, action="delete")
    return jsonify(DeleteOwnAccountResponse(success=result).to_dict()), 200
