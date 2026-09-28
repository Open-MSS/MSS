# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.admin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Internal endpoint used by the mscolab CLI to trigger the socket.io
    notifications connected clients would otherwise miss when the CLI mutates
    the database directly (see mslib.mscolab.seed). The CLI runs as its own
    process, separate from the running server, so it has no access to the
    live SocketsManager instance and cannot emit events itself.

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

import functools
import hmac
import logging

from flask import Blueprint, current_app, jsonify, request

from mslib.mscolab.api.events import SocketEvents

ADMIN_BP = Blueprint('admin', __name__)

# Only mscolab's own CLI, running on the same host as the server, may call this
# endpoint - it is not meant to be reachable over the network like the rest of
# the REST API, even though it shares the same Flask app/port.
_ALLOWED_REMOTE_ADDRS = {"127.0.0.1", "::1"}

# Maps a SocketEvents constant to the SocketsManager method that emits it and
# the integer payload fields that method expects, mirroring the REST handlers
# in blueprints/operation for the same events.
_NOTIFY_HANDLERS = {
    SocketEvents.REVOKE_PERMISSION: ("emit_revoke_permission", ("u_id", "op_id")),
    SocketEvents.OPERATION_PERMISSIONS_UPDATED: ("emit_operation_permissions_updated", ("u_id", "op_id")),
    SocketEvents.NEW_PERMISSION: ("emit_new_permission", ("u_id", "op_id")),
    SocketEvents.OPERATION_DELETED: ("emit_operation_delete", ("op_id",)),
    SocketEvents.UPDATE_OPERATION_LIST: ("emit_operation_list_update", ()),
}


def verify_admin_token(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if request.remote_addr not in _ALLOWED_REMOTE_ADDRS:
            logging.warning("Rejected %s from non-local address %s", request.path, request.remote_addr)
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        token = request.form.get('token', request.args.get('token', ''))
        if not hmac.compare_digest(token, current_app.config['ADMIN_TOKEN']):
            logging.warning("Rejected %s: bad admin token", request.path)
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper


@ADMIN_BP.route('/internal_notify', methods=['POST'])
@verify_admin_token
def internal_notify():
    event = request.form.get('event')
    handler = _NOTIFY_HANDLERS.get(event)
    if handler is None:
        return jsonify({"success": False, "message": f"Unknown event: {event}"}), 400
    method_name, arg_names = handler
    try:
        kwargs = {name: int(request.form[name]) for name in arg_names}
    except (KeyError, ValueError):
        return jsonify({"success": False, "message": "Missing or invalid arguments"}), 400
    sockio = current_app.extensions['sockio']
    getattr(sockio.sm, method_name)(**kwargs)
    if event == SocketEvents.REVOKE_PERMISSION:
        sockio.sm.remove_active_user_id_from_specific_operation(kwargs['u_id'], kwargs['op_id'])
    return jsonify({"success": True})
