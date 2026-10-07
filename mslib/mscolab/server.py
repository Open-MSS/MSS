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
import sys
from urllib.parse import urlsplit

from flask import request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

from mslib.mscolab.app import InsecureSecretError, create_app, initialise_db
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.sockets_manager import _setup_managers
from mslib.utils.basic_auth import BasicAuthSettingError, check_allowed_users, check_credentials


try:
    from mscolab_auth import mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mscolab_auth:
        allowed_users = []
        __file__ = None


# setup http auth
def authfunc(username, password):
    return check_credentials(mscolab_auth.allowed_users, username, password)


def verify_pw(username, password):
    if request.authorization:
        _auth = request.authorization
        username = _auth.username
        password = _auth.password
    return authfunc(username, password)


def _origin(url):
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _request_origins(environ):
    """The origins of the server as the request addressed it, also behind a proxy, as Engine.IO computes them"""
    origins = set()
    if "wsgi.url_scheme" in environ and "HTTP_HOST" in environ:
        origins.add(f"{environ['wsgi.url_scheme']}://{environ['HTTP_HOST']}")
        if "HTTP_X_FORWARDED_PROTO" in environ or "HTTP_X_FORWARDED_HOST" in environ:
            scheme = environ.get("HTTP_X_FORWARDED_PROTO", environ["wsgi.url_scheme"]).split(",")[0].strip()
            host = environ.get("HTTP_X_FORWARDED_HOST", environ["HTTP_HOST"]).split(",")[0].strip()
            origins.add(f"{scheme}://{host}")
    return origins


def cors_origins(config):
    """
    The origins of web pages that may send requests to the server from a browser

    CORS_ORIGINS, by default (None) the origin of SERVER_URL. Requests of the server's own pages are same-origin
    and need no CORS header.
    """
    origins = config.get("CORS_ORIGINS")
    return [_origin(config["SERVER_URL"])] if origins is None else origins


def socketio_allowed_origins(config):
    """
    cors_allowed_origins for Flask-SocketIO

    By default (CORS_ORIGINS None) the origin the request addressed the server with, which msui sends as Origin of
    its websocket, and the origin of SERVER_URL. A list of CORS_ORIGINS replaces both and has to contain the address
    msui users connect to; ["*"] allows every origin.
    """
    origins = config.get("CORS_ORIGINS")
    if origins is None:
        server_origin = _origin(config["SERVER_URL"])
        return lambda origin, environ: origin == server_origin or origin in _request_origins(environ)
    return "*" if "*" in origins else origins


def _initialize_managers(app):
    sockio, cm, fm = _setup_managers(app)
    app.extensions['cm'] = cm
    app.extensions['sockio'] = sockio
    app.extensions['fm'] = fm
    # initializing socketio, the configuration dependent options are passed here,
    # because _setup_managers creates the SocketIO instance without an app.
    sockio.init_app(app,
                    logger=app.config['SOCKETIO_LOGGER'],
                    engineio_logger=app.config['ENGINEIO_LOGGER'],
                    cors_allowed_origins=socketio_allowed_origins(app.config))
    return app, sockio, cm, fm


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

    CORS(app, origins=cors_origins(app.config))
    # Every app gets its own HTTPBasicAuth instance, so that apps existing side by side
    # (e.g. in the tests) cannot overwrite each other's authentication callback. The
    # callback is always registered; whether it is applied is decided per request from
    # ENABLE_BASIC_HTTP_AUTHENTICATION, see mslib.mscolab.auth.
    basic_auth = HTTPBasicAuth()
    basic_auth.verify_password(verify_pw)
    app.extensions["basic_auth"] = basic_auth
    if app.config.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
        logging.debug("Enabling basic HTTP authentication. Username and "
                      "password required to access the service.")
        check_allowed_users(mscolab_auth.allowed_users, "mscolab_auth")

    _initialize_managers(app)
    return app


def start_server(app, sockio, cm, fm, port=8083):
    sockio.run(app, port=port, debug=app.config['DEBUG'])


def main():
    try:
        app = create_server_app()
    except (InsecureSecretError, BasicAuthSettingError) as ex:
        # a configuration error, no traceback
        print(f"mscolab: {ex}", file=sys.stderr)
        sys.exit(1)
    start_server(app, app.extensions['sockio'], app.extensions['cm'], app.extensions['fm'])


if __name__ == '__main__':
    main()
