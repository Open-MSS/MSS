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
import socketio
import sqlalchemy.exc
import hashlib

from flask import jsonify, request, current_app
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from mslib.mscolab.app import create_app, APP
from mslib.mscolab.models import User
from mslib.mscolab.sockets_manager import _setup_managers


APP = create_app(imprint=APP.config['IMPRINT'], gdpr=APP.config['GDPR'])
CORS(APP, origins=APP.config.get('CORS_ORIGINS', ["*"]))
auth = HTTPBasicAuth()
with APP.app_context():
    current_app.extensions["basic_auth"] = auth


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


if APP.config.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    auth.verify_password(verify_pw)


def _initialize_managers(app):
    sockio, cm, fm = _setup_managers(app)
    app.extensions['cm'] = cm
    app.extensions['sockio'] = sockio
    app.extensions['fm'] = fm
    # initializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    # db.init_app(app)
    return app, sockio, cm, fm


_app, sockio, cm, fm = _initialize_managers(APP)


def check_login(emailid, password):
    try:
        user = User.query.filter_by(emailid=str(emailid)).first()
    except sqlalchemy.exc.OperationalError as ex:
        logging.debug("Problem in the database (%ex), likely version client different", ex)
        return False
    if user is not None:
        if APP.config['MAIL_ENABLED']:
            if user.confirmed:
                if user.verify_password(password):
                    return user
        else:
            if user.verify_password(password):
                return user
    return False


# 413: Payload Too Large
@APP.errorhandler(413)
def error413(error):
    upload_limit = APP.config['MAX_CONTENT_LENGTH'] / 1024 / 1024
    return jsonify({"success": False, "message": f"File size too large. Upload limit is {upload_limit}MB"}), 413


def start_server(app, sockio, cm, fm, port=8083):
    sockio.run(app, port=port, debug=APP.config['DEBUG'])


def main():
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)


if __name__ == '__main__':
    main()
