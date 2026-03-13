# -*- coding: utf-8 -*-
"""

    mslib.mscolab.app
    ~~~~~~~~~~~~~~~~~

    app module of mscolab

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
import sqlalchemy

from flask_migrate import Migrate
from flask import Flask, Blueprint

import mslib

from flask import render_template, send_from_directory, send_file, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from mslib.mscolab.conf import mscolab_settings
from mslib.utils import prefix_route, release_info
from mslib.msui.icons import icons
from mslib.utils.get_content import get_content
from xstatic.main import XStatic

message, update = release_info.check_for_new_release()
if update:
    logging.warning(message)


def file_exists(filepath=None):
    try:
        return os.path.isfile(filepath)
    except TypeError:
        return False


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_STATIC_DIR = os.path.join(DOCS_SERVER_PATH, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_STATIC_DIR, 'templates')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')

docs_bp = Blueprint(
    "docs",
    __name__,
    template_folder=os.path.join(DOCS_TEMPLATES_DIR)
)

# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_TEMPLATES_DIR))
APP.config.from_object(mscolab_settings)
# Expose docs path for callers/tests and make it part of Flask config for consistency.
APP.config['DOCS_SERVER_PATH'] = DOCS_SERVER_PATH
APP.route = prefix_route(APP.route, SCRIPT_NAME)


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


# Keep backward compatibility with callers/tests expecting an app attribute.
APP.xstatic = _xstatic


def create_app(imprint=None, gdpr=None):
    imprint_file = imprint
    gdpr_file = gdpr

    APP.jinja_env.globals.update(file_exists=file_exists)
    APP.jinja_env.globals["imprint"] = imprint_file
    APP.jinja_env.globals["gdpr"] = gdpr_file
    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    @docs_bp.route('/xstatic/<name>/<path:filename>')
    def files(name, filename):
        base_path = _xstatic(name)
        if base_path is None:
            abort(404)
        if not filename:
            abort(404)
        return send_from_directory(base_path, filename)

    @docs_bp.route('/mss_theme/img/<path:filename>')
    def mss_theme(filename):
        base_path = os.path.join(DOCS_IMG_DIR)
        return send_from_directory(base_path, filename)

    @docs_bp.route("/index")
    def index():
        return render_template("/index.html")

    @docs_bp.route("/mss/about")
    @docs_bp.route("/mss")
    def about():
        _file = os.path.join(DOCS_DOCS_DIR, 'about.md')
        img_url = url_for('docs.overview')
        md_overrides = ('![image](/mss/overview.png)', f'![image]({img_url})')

        html_overrides = ('<img alt="image" src="/mss/overview.png" />',
                          '<img class="mx-auto d-block img-fluid" alt="image" src="/mss/overview.png" />')
        content = get_content(_file, md_overrides=md_overrides, html_overrides=html_overrides)
        return render_template("/content.html", act="about", content=content)

    @docs_bp.route("/mss/install")
    def install():
        _file = os.path.join(DOCS_DOCS_DIR, 'installation.md')
        content = get_content(_file)
        return render_template("/content.html", act="install", content=content)

    @docs_bp.route("/mss/help")
    def help():  # noqa: A001
        _file = os.path.join(DOCS_DOCS_DIR, 'help.md')
        html_overrides = ('<img alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />',
                          '<img  class="mx-auto d-block img-fluid" alt="Waypoint Tutorial" '
                          'src="https://mss.readthedocs.io/en/stable/_images/tutorial_waypoints.gif" />')
        content = get_content(_file, html_overrides=html_overrides)
        return render_template("/content.html", act="help", content=content)

    @docs_bp.route("/mss/imprint")
    def imprint():
        if file_exists(imprint_file):
            content = get_content(imprint_file)
            return render_template("/content.html", act="imprint", content=content)
        else:
            return ""

    @docs_bp.route("/mss/gdpr")
    def gdpr():
        if file_exists(gdpr_file):
            content = get_content(gdpr_file)
            return render_template("/content.html", act="gdpr", content=content)
        else:
            return ""

    @docs_bp.route('/mss/favicon.ico')
    def favicons():
        base_path = icons("16x16", "favicon.ico")
        return send_file(base_path)

    @docs_bp.route('/mss/logo.png')
    def logo():
        base_path = icons("64x64", "mss-logo.png")
        return send_file(base_path)

    @docs_bp.route('/mss/overview.png')
    def overview():
        base_path = os.path.join(DOCS_IMG_DIR, 'wise12_overview.png')
        return send_file(base_path)
    APP.register_blueprint(docs_bp)
    return APP


db = SQLAlchemy(
    metadata=sqlalchemy.MetaData(
        naming_convention={
            # For reference: https://alembic.sqlalchemy.org/en/latest/naming.html#the-importance-of-naming-constraints
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    ),
)
db.init_app(APP)

migrate = Migrate(render_as_batch=True, user_module_prefix="cu.")
migrate.init_app(APP, db)


def get_topmenu():
    menu = [
        (url_for('docs.index'), 'Mission Support System',
         ((url_for('docs.about'), 'About'),
          (url_for('docs.install'), 'Install'),
          (url_for('docs.help'), 'Help'),
          )),
    ]
    return menu
