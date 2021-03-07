# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_user.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for user related routes.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.

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
import json
import sys
import time

from PyQt5 import QtWidgets
from mslib.mscolab.server import db, check_login, register_user
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import User
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9541, 9560))


class Test_UserMethods(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.1)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)

    def teardown(self):
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_registration(self):
        with self.app.app_context():
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x["success"] is True
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x["success"] is False
            x = register_user('sdf@ ssdf @s.com', 'sdf', 'sdf')
            assert x["success"] is False

    def test_login(self):
        with self.app.app_context():
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
        r = requests.post(self.url + '/register', data=data).json()
        assert r["success"] is True
        r = requests.post(self.url + '/register', data=data).json()
        assert r["success"] is False

    def test_token_api(self):
        data = {
            "email": "sdf@s1.com",
            "password": "sdf",
            "username": "sdf1"
        }
        r = requests.post(self.url + '/register', data=data)
        r = requests.post(self.url + '/token', data=data)
        json_ = json.loads(r.text)
        assert json_.get("token", None) is not None
        data["password"] = "asdf"
        r = requests.post(self.url + '/token', data=data)
        assert r.text == "False"
