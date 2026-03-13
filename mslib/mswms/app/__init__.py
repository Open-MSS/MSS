# -*- coding: utf-8 -*-
"""

    mslib.mswms.app
    ~~~~~~~~~~~~~~~

    app module of mswms

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
import logging
import mslib

from flask import Flask, url_for, render_template, send_from_directory, send_file, abort, Blueprint
from xstatic.main import XStatic
from mslib.msui.icons import icons

from mslib.mswms.gallery_builder import STATIC_LOCATION
from mslib.utils import prefix_route, release_info
from mslib.utils.file_exists import file_exists
from mslib.utils.get_content import get_content

DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_STATIC_DIR = os.path.join(DOCS_SERVER_PATH, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_STATIC_DIR, 'templates')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')

DOCS_BP = Blueprint(
    "docs",
    __name__,
    template_folder=os.path.join(DOCS_TEMPLATES_DIR)
)


class default_mswms_settings:
    # xml_templates live in the mswms package root, not the app subpackage.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    xml_template_location = os.path.join(base_dir, "xml_templates")
    service_name = "OGC:WMS"
    service_title = "Mission Support System Web Map Service"
    service_abstract = ""
    service_contact_person = ""
    service_contact_organisation = ""
    service_contact_position = ""
    service_address_type = ""
    service_address = ""
    service_city = ""
    service_state_or_province = ""
    service_post_code = ""
    service_country = ""
    service_fees = ""
    service_email = ""
    service_access_constraints = "This service is intended for research purposes only."
    register_horizontal_layers = []
    register_vertical_layers = []
    register_linear_layers = []
    imprint = ""
    gdpr = ""
    data = {}
    enable_basic_http_authentication = False
    __file__ = None


mswms_settings = default_mswms_settings()

message, update = release_info.check_for_new_release()
if update:
    logging.warning(message)


# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_TEMPLATES_DIR),
            static_url_path="/static",
            static_folder=STATIC_LOCATION)
APP.config.from_object(default_mswms_settings)
APP.route = prefix_route(APP.route, SCRIPT_NAME)

APP.jinja_env.globals.update(file_exists=file_exists)


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


def get_topmenu():
    menu = [
        (url_for('docs.index'), 'Mission Support System',
         ((url_for('docs.about'), 'About'),
          (url_for('docs.install'), 'Install'),
          (url_for('docs.help'), 'Help'),
          )),
    ]

    return menu


def create_app(name="", imprint=None, gdpr=None):
    imprint_file = imprint
    gdpr_file = gdpr

    APP.jinja_env.globals.update(file_exists=file_exists)
    APP.jinja_env.globals["imprint"] = imprint_file
    APP.jinja_env.globals["gdpr"] = gdpr_file
    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    @DOCS_BP.route('/xstatic/<name>/<path:filename>')
    def files(name, filename):
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
        return render_template("/index.html")

    @DOCS_BP.route("/mss/about")
    @DOCS_BP.route("/mss")
    def about():
        _file = os.path.join(DOCS_DOCS_DIR, 'about.md')
        img_url = url_for('docs.overview')
        md_overrides = ('![image](/mss/overview.png)', f'![image]({img_url})')

        html_overrrides = ('<img alt="image" src="/mss/overview.png" />',
                           '<img class="mx-auto d-block img-fluid" alt="image" src="/mss/overview.png" />')
        content = get_content(_file, md_overrides=md_overrides, html_overrides=html_overrrides)
        return render_template("/content.html", act="about", content=content)

    @DOCS_BP.route("/mss/install")
    def install():
        _file = os.path.join(DOCS_DOCS_DIR, 'installation.md')
        content = get_content(_file)
        return render_template("/content.html", act="install", content=content)

    @DOCS_BP.route("/mss/help")
    def help():  # noqa: A001
        _file = os.path.join(DOCS_DOCS_DIR, 'help.md')
        html_overrides = ('<img alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />',
                          '<img  class="mx-auto d-block img-fluid" alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />')
        content = get_content(_file, html_overrides=html_overrides)
        return render_template("/content.html", act="help", content=content)

    @DOCS_BP.route("/mss/imprint")
    def imprint():
        if file_exists(imprint_file):
            content = get_content(imprint_file)
            return render_template("/content.html", act="imprint", content=content)
        else:
            return ""

    @DOCS_BP.route("/mss/gdpr")
    def gdpr():
        if file_exists(gdpr_file):
            content = get_content(gdpr_file)
            return render_template("/content.html", act="gdpr", content=content)
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
    APP.register_blueprint(DOCS_BP)
    return APP
