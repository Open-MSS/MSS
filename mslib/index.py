# -*- coding: utf-8 -*-
"""

    mslib.index
    ~~~~~~~~~~~~

    shows some docs on the root url of the server

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2024 by the MSS team, see AUTHORS.
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
import mslib

from flask import render_template
from flask import send_from_directory, send_file, url_for
from flask import abort
from xstatic.main import XStatic
from mslib.msui.icons import icons
from mslib.utils.get_content import get_content

# set the operation root directory as the static folder
DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')


def _xstatic(name):
    mod_names = [
        'jquery', 'bootstrap',
    ]
    pkg = __import__('xstatic.pkg', fromlist=mod_names)
    serve_files = {}

    for mod_name in mod_names:
        mod = getattr(pkg, mod_name)
        # ToDo protocol should become configurable
        xs = XStatic(mod, root_url='/static', provider='local', protocol='http')
        serve_files[xs.name] = xs.base_dir
    try:
        return serve_files[name]
    except KeyError:
        return None


def file_exists(filepath=None):
    try:
        return os.path.isfile(filepath)
    except TypeError:
        return False


def create_app(name="", imprint=None, gdpr=None):
    imprint_file = imprint
    gdpr_file = gdpr

    if "mscolab.server" in name:
        from mslib.mscolab.app import APP, get_topmenu
    else:
        from mslib.mswms.app import APP, get_topmenu

    APP.jinja_env.globals.update(file_exists=file_exists)
    APP.jinja_env.globals["imprint"] = imprint_file
    APP.jinja_env.globals["gdpr"] = gdpr_file

    @APP.route('/xstatic/<name>/<path:filename>')
    def files(name, filename):
        base_path = _xstatic(name)
        if base_path is None:
            abort(404)
        if not filename:
            abort(404)
        return send_from_directory(base_path, filename)

    @APP.route('/mss_theme/img/<path:filename>')
    def mss_theme(filename):
        base_path = os.path.join(DOCS_SERVER_PATH, 'static', 'img')
        return send_from_directory(base_path, filename)

    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    @APP.route("/mss/about")
    @APP.route("/mss")
    def about():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'about.md')
        img_url = url_for('overview')
        md_overrides = ('![image](/mss/overview.png)', f'![image]({img_url})')

        html_overrrides = ('<img alt="image" src="/mss/overview.png" />',
                           '<img class="mx-auto d-block img-fluid" alt="image" src="/mss/overview.png" />')
        content = get_content(_file, md_overrides=md_overrides, html_overrides=html_overrrides)
        return render_template("/content.html", act="about", content=content)

    @APP.route("/mss/install")
    def install():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'installation.md')
        content = get_content(_file)
        return render_template("/content.html", act="install", content=content)

    @APP.route("/mss/help")
    def help():  # noqa: A001
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'help.md')
        html_overrides = ('<img alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />',
                          '<img  class="mx-auto d-block img-fluid" alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />')
        content = get_content(_file, html_overrides=html_overrides)
        return render_template("/content.html", act="help", content=content)

    @APP.route("/mss/imprint")
    def imprint():
        if file_exists(imprint_file):
            content = get_content(imprint_file)
            return render_template("/content.html", act="imprint", content=content)
        else:
            return ""

    @APP.route("/mss/gdpr")
    def gdpr():
        if file_exists(gdpr_file):
            content = get_content(gdpr_file)
            return render_template("/content.html", act="gdpr", content=content)
        else:
            return ""

    @APP.route('/mss/favicon.ico')
    def favicons():
        base_path = icons("16x16", "favicon.ico")
        return send_file(base_path)

    @APP.route('/mss/logo.png')
    def logo():
        base_path = icons("64x64", "mss-logo.png")
        return send_file(base_path)

    @APP.route('/mss/overview.png')
    def overview():
        base_path = os.path.join(DOCS_SERVER_PATH, 'static', 'img', 'wise12_overview.png')
        return send_file(base_path)

    return APP
