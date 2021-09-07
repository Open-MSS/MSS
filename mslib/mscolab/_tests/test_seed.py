# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_seed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for conf functionalities

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
from mslib.mscolab.models import db, User, Project
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.server import APP
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import (add_user, get_user, add_project, add_user_to_project,
                                delete_user, delete_project, add_all_users_default_project)


class Test_Seed(TestCase):
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
        db.init_app(self.app)
        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        self.room_name = "XYZ"
        self.description = "Template"
        self.userdata_0 = 'UV0@uv0', 'UV0', 'uv0'
        self.userdata_1 = "UV1@uv1", "UV1", "UV1"
        self.userdata_2 = "UV2@v2", "V2", "v2"

        assert add_user(self.userdata_0[0], self.userdata_0[1], self.userdata_0[2])
        assert add_project(self.room_name, self.description)
        assert add_user_to_project(path=self.room_name, emailid=self.userdata_0[0])
        self.user = User(self.userdata_0[0], self.userdata_0[1], self.userdata_0[2])

    def tearDown(self):
        pass

    def test_add_project(self):
        with self.app.test_client():
            assert add_project("a1", "description")
            project = Project.query.filter_by(path="a1").first()
            assert project.id > 0

    def test_delete_project(self):
        with self.app.test_client():
            assert add_project("todelete", "description")
            project = Project.query.filter_by(path="todelete").first()
            assert project.id > 0
            assert delete_project("todelete")
            project = Project.query.filter_by(path="todelete").first()
            assert project is None

    def test_add_all_users_default_project_viewer(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2])
            # viewer
            add_all_users_default_project(path='XYZ', description="Project to keep all users", access_level='viewer')
            expected_result = [{'access_level': 'viewer', 'category': 'default',
                                'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_collaborator(self):
        with self.app.test_client():
            # collaborator
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2])
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='collaborator')
            expected_result = [{'access_level': 'collaborator', 'category': 'default',
                                'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2])
            # creator
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'category': 'default',
                                'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator_unknown_project(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2])
            # creator added to new project
            add_all_users_default_project(path='UVXYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'category': 'default',
                                'description': 'Project to keep all users',
                                'p_id': 7, 'path': 'UVXYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_user(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2])
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2]) is False

    def test_get_user(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2])
            user = get_user(self.userdata_2[0])
            assert user.id is not None
            assert user.emailid == self.userdata_2[0]

    def test_add_user_to_project(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2])
            assert add_project("project2", "description")
            assert add_user_to_project(path="project2", access_level='admin', emailid=self.userdata_2[0])

    def test_delete_user(self,):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2])
            user = User.query.filter_by(emailid=self.userdata_2[0]).first()
            assert user is not None
            assert delete_user(self.userdata_2[0])
            user = User.query.filter_by(emailid=self.userdata_2[0]).first()
            assert user is None
