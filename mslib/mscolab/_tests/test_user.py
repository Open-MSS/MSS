# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_user.py
    ~~~~~~~~~~~~~~~~~~~~

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
from mslib.mscolab.server import db, check_login, register_user
from flask import Flask
from conf import SQLALCHEMY_DB_URI


class Test_UserMethods(object):

    def setup(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        self.app.config['SECRET_KEY'] = 'secret!'
        db.init_app(self.app)

    def test_registration(self):
        with self.app.app_context():
            # db.create_all()
            # self.populate_db()
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'True'
            x = register_user('sdf@s.com', 'sdf', 'sdf')
            assert x == 'False'

    def test_login(self):
        with self.app.app_context():
            # db.create_all()
            # self.populate_db()
            x = check_login('sdf@s.com', 'sdf')
            assert x is not None
            x = check_login('sdf@s.com', 'fd')
            assert x is not True

    def teardown(self):
        with self.app.app_context():
            user = check_login('sdf@s.com', 'sdf')
            if user:
                db.session.delete(user)
                db.session.commit()
