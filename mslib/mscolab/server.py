# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

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
import logging
import hashlib

from flask import current_app, jsonify, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from mslib.mscolab.app import create_app, initialise_db
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.sockets_manager import _setup_managers


auth = HTTPBasicAuth()


try:
    from mscolab_auth import mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mscolab_auth:
        allowed_users = [("mscolab", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None


# setup http auth
# for current test setup of test_server_auth_required we need the definition on module level
# so the import works regardless of when server was first loaded.
def authfunc(username, password):
    for u, p in mscolab_auth.allowed_users:
        if (u == username) and (p == hashlib.md5(password.encode('utf-8')).hexdigest()):
            return True
    return False


def verify_pw(username, password):
    if request.authorization:
        _auth = request.authorization
        username = _auth.username
        password = _auth.password
    return authfunc(username, password)


def _initialize_managers(app):
    sockio, cm, fm = _setup_managers(app)
    app.extensions['cm'] = cm
    app.extensions['sockio'] = sockio
    app.extensions['fm'] = fm
    # initializing socketio, the configuration dependent options are passed here,
    # because the SocketIO instance itself is created on import, without an app.
    sockio.init_app(app,
                    logger=app.config['SOCKETIO_LOGGER'],
                    engineio_logger=app.config['ENGINEIO_LOGGER'],
                    cors_allowed_origins=("*" if "*" in app.config['CORS_ORIGINS']
                                          else app.config['CORS_ORIGINS']))
    return app, sockio, cm, fm


# 413: Payload Too Large
def error413(error):
    upload_limit = current_app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024
    return jsonify({"success": False, "message": f"File size too large. Upload limit is {upload_limit}MB"}), 413


def create_server_app(config_object=mscolab_settings):
    """Create the MSColab application ready to be served.

    In addition to :func:`mslib.mscolab.app.create_app` this migrates the database
    to the latest revision and sets up everything only a served app needs: CORS,
    basic HTTP authentication and the socket.io managers. The managers are
    available as ``app.extensions['sockio' | 'cm' | 'fm']``.
    """
    app = create_app(config_object)
    with app.app_context():
        initialise_db()

    CORS(app, origins=app.config.get('CORS_ORIGINS', ["*"]))
    app.extensions["basic_auth"] = auth
    if app.config.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
        logging.debug("Enabling basic HTTP authentication. Username and "
                      "password required to access the service.")
        auth.verify_password(verify_pw)
    app.register_error_handler(413, error413)

    _initialize_managers(app)
    return app


def start_server(app, sockio, cm, fm, port=8083):
    sockio.run(app, port=port, debug=app.config['DEBUG'])


def main():
    app = create_server_app()
    start_server(app, app.extensions['sockio'], app.extensions['cm'], app.extensions['fm'])


if __name__ == '__main__':
    main()
