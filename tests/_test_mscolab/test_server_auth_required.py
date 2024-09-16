# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_server_auth_required
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server basics when auth is enabled

    This file is part of MSS.

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
import pytest

from mslib.mscolab.conf import mscolab_settings

mscolab_settings.enable_basic_http_authentication = True
try:
    from mslib.mscolab.server import authfunc, verify_pw, initialize_managers, get_auth_token, register_user
except ImportError:
    pytest.skip("this test runs only by an explicit call "
                "e.g. pytest tests/_test_mscolab/test_server_auth_required.py", allow_module_level=True)


class Test_Server_Auth_Not_Valid:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app):
        self.app = mscolab_app
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'

    def test_initialize_managers(self):
        app, sockio, cm, fm = initialize_managers(self.app)

        assert app.config['OPERATIONS_DATA'] == mscolab_settings.OPERATIONS_DATA
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_authfunc(self):
        mscolab_settings.enable_basic_http_authentication = True
        assert authfunc("user", "testvaluepassword")
        assert authfunc("user", "wrong") is False

    def test_verify_pw(self):
        assert verify_pw("user", "testvaluepassword")
        assert verify_pw("unknown", "unknown") is False
        assert verify_pw("user", "wrong") is False

    def test_register_user(self):
        r = register_user("test@test.io", "test", "pwdtest")
        assert r.status_code == 401

    def test_get_auth_token(self):
        r = get_auth_token()
        assert r.status_code == 401
