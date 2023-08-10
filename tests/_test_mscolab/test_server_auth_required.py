# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_server_auth_required
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server basics when auth is enabled

    This file is part of MSS.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2023 by the MSS team, see AUTHORS.
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
import pytest

from flask_testing import TestCase
from mslib.mscolab.conf import mscolab_settings

mscolab_settings.enable_basic_http_authentication = True
try:
    from mslib.mscolab.server import authfunc, verify_pw, initialize_managers, get_auth_token, register_user, APP
except ImportError:
    pytest.skip("this test runs only by an explicit call "
                "e.g. pytest tests/_test_mscolab/test_server_auth_required.py", allow_module_level=True)

from mslib.mscolab.mscolab import handle_db_reset


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Server_Auth_Not_Valid(TestCase):
    render_templates = False

    def create_app(self):
        app = APP
        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['LIVESERVER_PORT'] = 0
        return app

    def setUp(self):
        handle_db_reset()
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'

    def tearDown(self):
        pass

    def test_initialize_managers(self):
        app, sockio, cm, fm = initialize_managers(self.app)

        assert app.config['MSCOLAB_DATA_DIR'] == mscolab_settings.MSCOLAB_DATA_DIR
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_authfunc(self):
        mscolab_settings.enable_basic_http_authentication = True
        assert authfunc("user", "testvaluepassword")
        assert authfunc("user", "wrong") is False

    def test_verify_pw(self):
        assert verify_pw("user", "testvaluepassword")
        assert verify_pw("unknown", "unknow") is False
        assert verify_pw("user", "wrong") is False

    def test_register_user(self):
        r = register_user("test@test.io", "test", "pwdtest")
        assert r.status_code == 401

    def test_get_auth_token(self):
        r = get_auth_token()
        assert r.status_code == 401
