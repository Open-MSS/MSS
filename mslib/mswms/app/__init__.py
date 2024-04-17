# -*- coding: utf-8 -*-
"""

    mslib.mswms.app
    ~~~~~~~~~~~~~~~

    app module of mswms

    This file is part of MSS.

    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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

from flask import Flask
from mslib.mswms.gallery_builder import STATIC_LOCATION
from mslib.utils import prefix_route


DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')

# in memory database for testing
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
APP = Flask(__name__, template_folder=os.path.join(DOCS_SERVER_PATH, 'static', 'templates'), static_url_path="/static",
            static_folder=STATIC_LOCATION)
APP.config.from_object(__name__)
APP.route = prefix_route(APP.route, SCRIPT_NAME)
