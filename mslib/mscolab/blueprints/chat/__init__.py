# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Chat Blueprint for server for mscolab module

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

import werkzeug
from flask import Blueprint, request, g, jsonify, abort, send_from_directory, current_app

from mslib.mscolab.auth import verify_user
from mslib.mscolab.events import SocketEvents
from mslib.mscolab.message_type import MessageType
from mslib.mscolab.utils import ATTACHMENTS_URL_PREFIX, get_message_dict

CHAT_BP = Blueprint('chat', __name__)


@CHAT_BP.route("/messages", methods=["GET"])
@verify_user
def messages():
    fm = current_app.extensions['fm']
    user = g.user
    op_id = request.args.get("op_id", request.form.get("op_id", None))

    if fm.is_member(user.id, op_id):
        cm = current_app.extensions['cm']
        timestamp = request.args.get("timestamp", request.form.get("timestamp", "1970-01-01T00:00:00+00:00"))
        chat_messages = cm.get_messages(op_id, timestamp)
        return jsonify({"messages": chat_messages})
    return "False"


@CHAT_BP.route("/message_attachment", methods=["POST"])
@verify_user
def message_attachment():
    user = g.user
    op_id = request.form.get("op_id", None)
    fm = current_app.extensions['fm']
    if fm.is_member(user.id, op_id) and not fm.is_viewer(user.id, op_id):
        file = request.files['file']
        message_type = MessageType(int(request.form.get("message_type")))
        user = g.user
        if file is not None:
            static_file_path = fm.upload_file(file, subfolder=str(op_id), include_prefix=True)
            if static_file_path is not None:
                cm = current_app.extensions['cm']
                sockio = current_app.extensions['sockio']
                new_message = cm.add_message(user, static_file_path, op_id, message_type)
                new_message_dict = get_message_dict(new_message)
                sockio.emit(SocketEvents.CHAT_MESSAGE_CLIENT, json.dumps(new_message_dict))
                return jsonify({"success": True, "path": static_file_path})
            else:
                return "False"
        return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
    # normal use case never gets to this
    return "False"


@CHAT_BP.route(f'/{ATTACHMENTS_URL_PREFIX}/<name>/<path:filename>', methods=["GET"])
def uploads(name=None, filename=None):
    base_path = current_app.config['UPLOAD_FOLDER']
    if name is None:
        abort(404)
    if filename is None:
        abort(404)
    return send_from_directory(base_path, werkzeug.security.safe_join("", name, filename))
