# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.docs
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docs Blueprint for app module of mscolab

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

import os
from functools import wraps

from flask import Blueprint, abort, send_from_directory, render_template, url_for, send_file, current_app
from flask_httpauth import HTTPBasicAuth

from mslib.msui.icons import icons
from mslib.utils.file_exists import file_exists
from mslib.utils.get_content import get_content

DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(__file__))
DOCS_STATIC_DIR = os.path.join(DOCS_SERVER_PATH, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')

DOCS_BP = Blueprint("docs", __name__, template_folder='templates', static_folder='static', static_url_path='/static')
auth_basic_auth = HTTPBasicAuth()


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get('enable_basic_http_authentication', False):
            return auth_basic_auth.login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated


@DOCS_BP.route('/')
@optional_auth
def home():
    return render_template("docs/index.html")


@DOCS_BP.route('/xstatic/<name>/<path:filename>')
def files(name, filename):
    from mslib.mscolab.app import _xstatic
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
    html_overrides = ('<img alt="Waypoint Tutorial" '
                      'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />',
                      '<img  class="mx-auto d-block img-fluid" alt="Waypoint Tutorial" '
                      'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />')
    content = get_content(_file, html_overrides=html_overrides)
    return render_template("docs/content.html", act="help", content=content)


@DOCS_BP.route("/mss/imprint")
def imprint(imprint_file=None):
    if file_exists(imprint_file):
        content = get_content(imprint_file)
        return render_template("docs/content.html", act="imprint", content=content)
    else:
        return ""


@DOCS_BP.route("/mss/gdpr")
def gdpr(gdpr_file=None):
    if file_exists(gdpr_file):
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
