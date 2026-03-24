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

from flask import Flask, url_for
from xstatic.main import XStatic
from mslib.mswms.blueprints.docs import DOCS_BP

from mslib.mswms.gallery_builder import STATIC_LOCATION
from mslib.utils import prefix_route, release_info
from mslib.utils.file_exists import file_exists

DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
DOCS_STATIC_DIR = os.path.join(DOCS_SERVER_PATH, 'static')
DOCS_IMG_DIR = os.path.join(DOCS_STATIC_DIR, 'img')
DOCS_DOCS_DIR = os.path.join(DOCS_STATIC_DIR, 'docs')
DOCS_TEMPLATES_DIR = os.path.join(DOCS_STATIC_DIR, 'templates')
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')


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

    APP.register_blueprint(DOCS_BP)
    return APP
