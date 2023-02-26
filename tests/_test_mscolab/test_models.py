# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    api integration tests for models

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2022 by the MSS team, see AUTHORS.
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

from flask_testing import TestCase
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.server import register_user, APP
from mslib.mscolab.models import User


class Test_User(TestCase):
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
        result = register_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert result["success"] is True

    def test_generate_auth_token(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        token = user.generate_auth_token()
        assert token is not None
        assert len(token) > 20

    def test_verify_auth_token(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        token = user.generate_auth_token()
        id = user.verify_auth_token(token)
        assert user.id == id

    def test_verify_password(self):
        user = User(self.userdata[0], self.userdata[1], self.userdata[2])
        assert user.verify_password("fail") is False
        assert user.verify_password(self.userdata[2]) is True
