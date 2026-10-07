# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_server_auth_required
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server basics when auth is enabled

    This file is part of MSS.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2026 by the MSS team, see AUTHORS.
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
import base64

import pytest

import mslib.mscolab.server
from mslib.utils.basic_auth import PasswordCheckBusy
from mslib.mscolab.server import authfunc, verify_pw, _initialize_managers


class Test_Server_Auth_Not_Valid:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app):
        self.app = mscolab_app
        self.userdata = 'UV10@uv10', 'UV10', 'uv10', 'User UV'
        # Enable basic auth. The app is created freshly for every test, so this does not
        # leak into any other test.
        self.app.config['ENABLE_BASIC_HTTP_AUTHENTICATION'] = True

    def test_initialize_managers(self):
        app, sockio, cm, fm = _initialize_managers(self.app)

        assert app is self.app
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_authfunc(self):
        assert authfunc("user", "testvaluepassword")
        assert authfunc("user", "wrong") is False
        assert authfunc("unknown", "testvaluepassword") is False
        assert authfunc("user", None) is False

    def test_busy_password_checks_answer_503(self, monkeypatch):
        def busy(*args):
            raise PasswordCheckBusy("busy")

        monkeypatch.setattr(mslib.mscolab.server, "check_credentials", busy)
        credentials = base64.b64encode(b"user:testvaluepassword").decode("ascii")
        with self.app.test_client() as test_client:
            response = test_client.get("/status", headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "10"

    def test_authfunc_md5_digest_still_works(self):
        assert authfunc("md5user", "md5password")
        assert authfunc("md5user", "wrong") is False
        assert authfunc("user", "md5password") is False

    def test_verify_pw(self):
        with self.app.test_request_context():
            assert verify_pw("user", "testvaluepassword")
            assert verify_pw("unknown", "unknown") is False
            assert verify_pw("user", "wrong") is False

    def test_register_user(self):
        with self.app.test_client() as test_client:
            response = test_client.post('/register', data={"email": "test@test.io",
                                                           "password": "test",
                                                           "username": "UserPWD",
                                                           "fullname": "UserPWD"})
            assert response.status_code == 401

    def test_get_auth_token(self):
        with self.app.test_client() as test_client:
            response = test_client.post('/token', data={"email": "test@test.io",
                                                        "password": "test"})
        assert response.status_code == 401

    @pytest.mark.parametrize("username, password", [("user", "testvaluepassword"), ("md5user", "md5password")])
    def test_basic_auth_login_passes(self, username, password):
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        with self.app.test_client() as test_client:
            response = test_client.post('/token', data={"email": "test@test.io", "password": "test"},
                                        headers={"Authorization": f"Basic {credentials}"})
            assert response.status_code == 200
            wrong = base64.b64encode(f"{username}:wrong".encode()).decode()
            response = test_client.post('/token', data={"email": "test@test.io", "password": "test"},
                                        headers={"Authorization": f"Basic {wrong}"})
            assert response.status_code == 401
