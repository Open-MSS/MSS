# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_user.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for user related routes.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi

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
import requests
import multiprocessing
import json
import time

from mslib.mscolab.server import db, check_login, register_user, sockio, app
from mslib.mscolab.models import User


class Test_UserMethods(object):

    def setup(self):
        self._app = app
        db.init_app(self._app)
        self.thread = multiprocessing.Process(
            target=sockio.run,
            args=(app,),
            kwargs={'port': 8083})
        self.thread.start()
        time.sleep(1)

    def test_registration(self):
        with self._app.app_context():
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'True'
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'False'

    def test_login(self):
        with self._app.app_context():
            x = check_login('sdf@s.com', 'sdf')
            assert x is not None
            x = check_login('sdf@s.com', 'fd')
            assert x is not True

    def test_registration_api(self):
        data = {
            "email": "sdf@s1.com",
            "password": "sdf",
            "username": "sdf1"
        }
        r = requests.post('http://localhost:8083/register', data=data)
        assert r.text == "True"
        r = requests.post('http://localhost:8083/register', data=data)
        assert r.text == "False"

    def test_token_api(self):
        data = {
            "email": "sdf@s1.com",
            "password": "sdf",
            "username": "sdf1"
        }
        r = requests.post('http://localhost:8083/register', data=data)
        r = requests.post('http://localhost:8083/token', data=data)
        json_ = json.loads(r.text)
        assert json_.get("token", None) is not None
        data["password"] = "asdf"
        r = requests.post('http://localhost:8083/token', data=data)
        assert r.text == "False"

    def teardown(self):
        with self._app.app_context():
            User.query.filter_by(emailid="sdf@s.com").delete()
            User.query.filter_by(emailid="sdf@s1.com").delete()
            db.session.commit()
        self.thread.terminate()
