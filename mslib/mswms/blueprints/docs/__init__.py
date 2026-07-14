# -*- coding: utf-8 -*-
"""

    mslib.mswms.blueprints.docs
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docs Blueprint for app module of mswms

    This file is part of MSS.

    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import hashlib
import hmac
import logging
import os
import traceback
import urllib.parse
from functools import wraps

from flask import Blueprint, abort, send_from_directory, render_template, url_for, send_file, request, make_response, \
    current_app, Response
from multidict import CIMultiDict

from mslib.msui.icons import icons
from mslib.utils.file_exists import file_exists
from mslib.utils.get_content import get_content

DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(__file__))
DOCS_STATIC_DIR = os.path.join(DOCS_SERVER_PATH, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')

DOCS_BP = Blueprint("docs", __name__, template_folder='templates',
                    static_folder='static', static_url_path='/docs-static')


def basic_auth(allowed_users):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.authorization

            if not auth:
                return Response(
                    "Authentication required",
                    401,
                    {"WWW-Authenticate": 'Basic realm="Login Required"'},
                )

            password_hash = hashlib.md5(auth.password.encode()).hexdigest()

            authenticated = any(
                hmac.compare_digest(auth.username, username)
                and hmac.compare_digest(password_hash, stored_hash)
                for username, stored_hash in allowed_users
            )

            if not authenticated:
                return Response(
                    "Authentication required",
                    401,
                    {"WWW-Authenticate": 'Basic realm="Login Required"'},
                )

            return f(*args, **kwargs)

        return wrapper

    return decorator


def build_auth_backend(enabled, allowed_users):
    def auth_backend(view):
        if not enabled:
            return view

        return basic_auth(allowed_users)(view)

    return auth_backend


def init_docs_bp(app, auth_backend):
    view = auth_backend(_application_impl)
    app.add_url_rule("/", view_func=view)


def _application_impl():
    try:
        # Request info
        query = CIMultiDict(request.args)
        # Processing
        # ToDo Refactor
        request_type = query.get('request')
        if request_type is None:  # request_type may *actually* be set to None
            request_type = ''
        request_type = request_type.lower()
        request_service = query.get('service', '')
        request_service = request_service.lower()
        request_version = query.get('version', '')

        url = request.url
        server_url = urllib.parse.urljoin(url, urllib.parse.urlparse(url).path)

        from mslib.mswms.wms import server
        if (request_type in ('getcapabilities', 'capabilities') and
                request_service == 'wms' and request_version in ('1.1.1', '1.3.0', '')):
            return_data, mime_type = server.get_capabilities(query, server_url)
        elif request_type in ('getmap', 'getvsec', 'getlsec') and request_version in ('1.1.1', '1.3.0', ''):
            return_data, mime_type = server.produce_plot(query, request_type)
        else:
            logging.debug("Request type '%s' is not valid.", request)
            raise RuntimeError("Request type is not valid.")

        res = make_response(return_data, 200)
        response_headers = [('Content-type', mime_type), ('Content-Length', str(len(return_data)))]
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]

        return res

    except Exception as ex:
        # without query parameter show index page
        query = request.args
        if len(query) == 0:
            return render_template("docs/index.html")

        # communicate request errors back to client user
        logging.error("Unexpected error: %s: %s\nTraceback:\n%s",
                      type(ex), ex, traceback.format_exc())
        error_message = "{}: {}\n".format(type(ex), ex)
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(error_message)))]
        res = make_response(error_message, 404)
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]
        return res


@DOCS_BP.route('/xstatic/<name>/<path:filename>')
def files(name, filename):
    from mslib.mswms.app import _xstatic
    base_path = _xstatic(name)
    if base_path is None:
        abort(404)
    if not filename:
        abort(404)
    return send_from_directory(base_path, filename)


@DOCS_BP.route('/mss_theme/img/<path:filename>')
def mss_theme(filename):
    base_path = os.path.join(DOCS_IMG_DIR)
    return send_from_directory(base_path, filename)


@DOCS_BP.route("/index")
def index():
    return render_template("docs/index.html")


@DOCS_BP.route("/mss/about")
@DOCS_BP.route("/mss")
def about():
    _file = os.path.join(DOCS_DOCS_DIR, 'about.md')
    img_url = url_for('docs.overview')
    md_overrides = ('![image](/mss/overview.png)', f'![image]({img_url})')

    html_overrides = ('<img alt="image" src="/mss/overview.png" />',
                      '<img class="mx-auto d-block img-fluid" alt="image" src="/mss/overview.png" />')
    content = get_content(_file, md_overrides=md_overrides, html_overrides=html_overrides)
    return render_template("docs/content.html", act="about", content=content)


@DOCS_BP.route("/mss/install")
def install():
    _file = os.path.join(DOCS_DOCS_DIR, 'installation.md')
    content = get_content(_file)
    return render_template("docs/content.html", act="install", content=content)


@DOCS_BP.route("/mss/help")
def help():  # noqa: A001
    _file = os.path.join(DOCS_DOCS_DIR, 'help.md')
    md_overrides = ('![Waypoint Tutorial](https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.mp4)',
                    '<video class="mx-auto d-block img-fluid" controls preload="metadata">'
                    '<source src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.mp4" '
                    'type="video/mp4">Your browser does not support the video tag.</video>')
    content = get_content(_file, md_overrides=md_overrides)
    return render_template("docs/content.html", act="help", content=content)


@DOCS_BP.route("/mss/imprint")
def imprint():
    imprint_file = current_app.config.get('IMPRINT', None)
    if imprint_file is not None and file_exists(imprint_file):
        content = get_content(imprint_file)
        return render_template("docs/content.html", act="imprint", content=content)
    else:
        return ""


@DOCS_BP.route("/mss/gdpr")
def gdpr():
    gdpr_file = current_app.config.get('GDPR', None)
    if gdpr_file is not None and file_exists(gdpr_file):
        content = get_content(gdpr_file)
        return render_template("docs/content.html", act="gdpr", content=content)
    else:
        return ""


@DOCS_BP.route('/mss/favicon.ico')
def favicons():
    base_path = icons("16x16", "favicon.ico")
    return send_file(base_path)


@DOCS_BP.route('/mss/logo.png')
def logo():
    base_path = icons("64x64", "mss-logo.png")
    return send_file(base_path)


@DOCS_BP.route('/mss/overview.png')
def overview():
    base_path = os.path.join(DOCS_IMG_DIR, 'wise12_overview.png')
    return send_file(base_path)
