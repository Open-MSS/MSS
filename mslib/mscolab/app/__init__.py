# -*- coding: utf-8 -*-
"""

    mslib.mscolab.app
    ~~~~~~~~~~~~~~~~~

    app module of mscolab

    This file is part of MSS.

    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

from flask_migrate import Migrate

import mslib

from flask import Flask, url_for
from mslib.mscolab.conf import mscolab_settings
from flask_sqlalchemy import SQLAlchemy
from mslib.utils import prefix_route


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')

# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_SERVER_PATH, 'static', 'templates'))
APP.config.from_object(__name__)
APP.route = prefix_route(APP.route, SCRIPT_NAME)

APP.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
APP.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
APP.config['MAX_CONTENT_LENGTH'] = mscolab_settings.MAX_UPLOAD_SIZE
APP.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY
APP.config['SECURITY_PASSWORD_SALT'] = getattr(mscolab_settings, "SECURITY_PASSWORD_SALT", None)
APP.config['MAIL_DEFAULT_SENDER'] = getattr(mscolab_settings, "MAIL_DEFAULT_SENDER", None)
APP.config['MAIL_SERVER'] = getattr(mscolab_settings, "MAIL_SERVER", None)
APP.config['MAIL_PORT'] = getattr(mscolab_settings, "MAIL_PORT", None)
APP.config['MAIL_USERNAME'] = getattr(mscolab_settings, "MAIL_USERNAME", None)
APP.config['MAIL_PASSWORD'] = getattr(mscolab_settings, "MAIL_PASSWORD", None)
APP.config['MAIL_USE_TLS'] = getattr(mscolab_settings, "MAIL_USE_TLS", None)
APP.config['MAIL_USE_SSL'] = getattr(mscolab_settings, "MAIL_USE_SSL", None)

db = SQLAlchemy(APP)
migrate = Migrate(APP, db, render_as_batch=True)


def get_topmenu():
    menu = [
        (url_for('index'), 'Mission Support System',
         ((url_for('about'), 'About'),
          (url_for('install'), 'Install'),
          (url_for('help'), 'Help'),
          )),
    ]
    return menu
