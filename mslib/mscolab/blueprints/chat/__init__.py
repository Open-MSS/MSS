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


import io

import werkzeug
from PIL import Image
from flask import Blueprint, request, g, jsonify, abort, send_from_directory, current_app

from mslib.mscolab.auth import verify_user, verify_user_http
from mslib.mscolab.api.message_type import MessageType
from mslib.mscolab.utils import ATTACHMENTS_URL_PREFIX
from mslib.mscolab.api import endpoints
from mslib.mscolab.api.attachments import IMAGE_FORMATS, file_extension, normalized_extensions
from mslib.mscolab.api.schemas import (
    GetMessagesRequest,
    GetMessagesResponse,
    MessageAttachmentRequest,
    MessageAttachmentResponse,
)

CHAT_BP = Blueprint('chat', __name__)


@CHAT_BP.route(f"/{endpoints.MESSAGES}", methods=["GET"])
@verify_user
def messages():
    fm = current_app.extensions['fm']
    user = g.user
    req = GetMessagesRequest.from_args_and_form(request.args, request.form)

    if fm.is_member(user.id, req.op_id):
        cm = current_app.extensions['cm']
        chat_messages = cm.get_messages(req.op_id, req.timestamp)
        return jsonify(GetMessagesResponse(messages=chat_messages).to_dict())
    return "False"


@CHAT_BP.route(f"/{endpoints.MESSAGE_ATTACHMENT}", methods=["POST"])
@verify_user
def message_attachment():
    user = g.user
    req = MessageAttachmentRequest.from_form(request.form)
    fm = current_app.extensions['fm']
    # viewers can't send, and nothing can be sent to the read-only chat of an archived operation
    if fm.may_write(user.id, req.op_id):
        # an attachment is an image or a document, a TEXT one could be edited to point elsewhere and
        # a SYSTEM_MESSAGE one could not be deleted by its author
        if req.message_type not in (MessageType.IMAGE, MessageType.DOCUMENT):
            response = MessageAttachmentResponse(success=False, message="Invalid message type for an attachment.")
            return jsonify(response.to_dict())
        file = request.files.get('file')
        message_type = MessageType(req.message_type)
        user = g.user
        if file is not None:
            refused = _refused_attachment(file, message_type)
            if refused is not None:
                return jsonify(MessageAttachmentResponse(success=False, message=refused).to_dict())
            static_file_path = fm.upload_file(file, subfolder=str(req.op_id), include_prefix=True)
            if static_file_path is not None:
                cm = current_app.extensions['cm']
                sockio = current_app.extensions['sockio']
                new_message = cm.add_message(user, static_file_path, req.op_id, message_type)
                sockio.sm.emit_chat_message(new_message)
                return jsonify(MessageAttachmentResponse(success=True, path=static_file_path).to_dict())
            else:
                return "False"
        response = MessageAttachmentResponse(success=False, message="Could not send message. No file uploaded.")
        return jsonify(response.to_dict())
    # normal use case never gets to this
    return "False"


def _refused_attachment(file, message_type):
    """
    Why an attachment is refused, None if it is accepted

    Only the extensions of the setting MSCOLAB_ATTACHMENT_EXTENSIONS are accepted, an image has to be one.
    """
    extension = file_extension(file.filename)
    if extension == "":
        return "Files without an extension can not be sent."
    if extension not in normalized_extensions(current_app.config['MSCOLAB_ATTACHMENT_EXTENSIONS']):
        return f"Files of type .{extension} can not be sent."
    if message_type == MessageType.IMAGE:
        try:
            image = Image.open(io.BytesIO(file.read()))
            image.verify()
        except Exception:
            return "The image is no valid image."
        finally:
            file.seek(0)
        if image.format not in IMAGE_FORMATS:
            return f"Images of format {image.format} can not be sent."
    return None


@CHAT_BP.route(f'/{ATTACHMENTS_URL_PREFIX}/<name>/<path:filename>', methods=["GET"])
@verify_user_http
def uploads(name=None, filename=None):
    base_path = current_app.config['UPLOAD_FOLDER']
    if name is None:
        abort(404)
    if filename is None:
        abort(404)
    # name is the id of the operation the attachment was sent to, only its members may fetch it,
    # isdigit alone accepts digits like "²" which int() refuses
    if not (name.isascii() and name.isdigit()) or not current_app.extensions['fm'].is_member(g.user.id, int(name)):
        abort(404)
    # attachments are uploaded by any member, e.g. HTML or SVG files, a browser must not render them
    # as a page of the MSColab server
    response = send_from_directory(base_path, werkzeug.security.safe_join("", name, filename), as_attachment=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "sandbox"
    return response
