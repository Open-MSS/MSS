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
from flask import Flask

import mslib

from flask import url_for
from flask_sqlalchemy import SQLAlchemy

from mslib.mscolab.blueprints.docs import DOCS_BP
from mslib.mscolab.conf import mscolab_settings
from mslib.utils import prefix_route, release_info
from mslib.utils.file_exists import file_exists
from xstatic.main import XStatic


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_BLUEPRINTS_DIR = os.path.join(DOCS_SERVER_PATH, 'blueprints')
DOCS_BLUEPRINTS_DOCS_DIR = os.path.join(DOCS_BLUEPRINTS_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'templates')
DOCS_STATIC_DIR = os.path.join(DOCS_BLUEPRINTS_DOCS_DIR, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')


message, update = release_info.check_for_new_release()
if update:
    logging.warning(message)


# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_TEMPLATES_DIR))
APP.jinja_env.globals.setdefault("imprint", "")
APP.jinja_env.globals.setdefault("gdpr", "")
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
    APP.jinja_env.globals["imprint"] = imprint_file or ""
    APP.jinja_env.globals["gdpr"] = gdpr_file or ""
    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    from mslib.mscolab.blueprints.auth import AUTH_BP
    from mslib.mscolab.blueprints.chat import CHAT_BP
    from mslib.mscolab.blueprints.operation import OPERATION_BP
    from mslib.mscolab.blueprints.user import USER_BP

    APP.register_blueprint(AUTH_BP)
    APP.register_blueprint(CHAT_BP)
    APP.register_blueprint(USER_BP)
    APP.register_blueprint(OPERATION_BP)
    APP.register_blueprint(DOCS_BP)

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
