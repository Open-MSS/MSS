# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat functionalities

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
import socketio
import requests
import subprocess
import json
import logging
import os
from flask import Flask
import datetime

from mslib.mscolab.conf import SQLALCHEMY_DB_URI, MSCOLAB_DATA_DIR
from mslib.mscolab.models import db, User, Project
from mslib.mscolab.sockets_manager import fm
from mslib._tests.constants import MSCOLAB_URL_TEST


class Test_Files(object):
    def setup(self):
        self.sockets = []
        cwd = os.getcwd()
        path_to_server = cwd + "/mslib/mscolab/server.py"
        self.proc = subprocess.Popen(["python", path_to_server], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        try:
            outs, errs = self.proc.communicate(timeout=4)
        except Exception as e:
            logging.debug("Server isn't running")
            logging.debug(e)
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        db.init_app(self.app)
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()
    
    def test_create_project(self):
        with self.app.app_context():
            fm.create_project('test_path', 'test message', self.user)
            # check file existence
            assert os.path.exists(os.path.join(MSCOLAB_DATA_DIR, 'test_path')) == True
            # check creation in db
            p = Project.query.filter_by(path="test_path")
            assert p != None

    def test_projects(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            assert len(projects) == 3

    def test_add_permission(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert fm.add_permission(p_id, 9, 'collaborator', self.user) == True
            user2 = User.query.filter_by(id=9).first()
            projects = fm.list_projects(user2)
            assert len(projects) == 3

    def test_modify_permission(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert fm.update_access_level(p_id, 9, 'viewer', self.user) == True
            user2 = User.query.filter_by(id=9).first()
            projects = fm.list_projects(user2)
            assert projects[-1]["access_level"] == "viewer"

    def test_revoke_permission(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert fm.revoke_permission(p_id, 9, self.user) == True
            user2 = User.query.filter_by(id=9).first()
            projects = fm.list_projects(user2)
            assert len(projects) == 2


    def test_get_project(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert fm.get_file(p_id, self.user) != False
            user2 = User.query.filter_by(id=9).first()
            assert fm.get_file(p_id, user2) == False

    def test_authorized_users(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert len(fm.get_authorized_users(p_id)) == 1

    def test_modify_project(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            # ToDo when moving files, it should be able to change paths as well
            assert fm.update_project(p_id, 'path', 'dummy', self.user) == False
            assert fm.update_project(p_id, 'description', 'dummy', self.user) == True

    def test_delete_project(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            p_id = projects[-1]["p_id"]
            assert fm.delete_file(p_id, self.user) == True
            assert fm.delete_file(p_id, self.user) == False

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
            self.proc.kill()
