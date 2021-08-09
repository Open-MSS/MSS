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
from flask import Flask
from mslib.mscolab.models import User, Project, db
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.seed import add_user, add_project, add_user_to_project,\
    delete_user, delete_project, add_all_users_default_project
from mslib.mscolab.mscolab import handle_db_seed


class Test_Seed():
    def setup(self):
        handle_db_seed()
        self.app = Flask(__name__, static_url_path='')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        self.room_name = "XYZ"
        self.description = "Template"
        self.userdata = 'UV0@uv0', 'UV0', 'uv0'

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_project(self.room_name, self.description)
        assert add_user_to_project(path=self.room_name, emailid=self.userdata[0])
        self.user = User(self.userdata[0], self.userdata[1], self.userdata[2])

    def teardown(self):
        delete_user("UV0@uv0")
        delete_user("UV1@uv1")
        delete_user("UV2@uv2")
        delete_project("a1")
        delete_project("XYZ")
        delete_project("UXYZ")

    def test_add_project(self):
        with self.app.app_context():
            assert add_project("a1", "description")
            project = Project.query.filter_by(path="a1").first()
            assert project.id > 0

    def test_delete_project(self):
        with self.app.app_context():
            assert add_project("todelete", "description")
            project = Project.query.filter_by(path="todelete").first()
            assert project.id > 0
            assert delete_project("todelete")
            project = Project.query.filter_by(path="todelete").first()
            assert project is None

    def test_add_all_users_default_project_viewer(self):
        with self.app.app_context():
            assert add_user("UV1@uv1", "UV1", "UV1")
            # viewer
            add_all_users_default_project(path='XYZ', description="Project to keep all users", access_level='viewer')
            expected_result = [{'access_level': 'viewer', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_collaborator(self):
        with self.app.app_context():
            # collaborator
            assert add_user("UV1@uv1", "UV1", "UV1")
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='collaborator')
            expected_result = [{'access_level': 'collaborator', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator(self):
        with self.app.app_context():
            assert add_user("UV1@uv1", "UV1", "UV1")
            # creator
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator_unknown_project(self):
        with self.app.app_context():
            assert add_user("UV1@uv1", "UV1", "UV1")
            # creator added to new project
            add_all_users_default_project(path='UVXYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'description': 'Project to keep all users',
                                'p_id': 7, 'path': 'UVXYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_user(self):
        self.app.app_context().push()
        assert add_user("UV2@v2", "V2", "v2")
        assert add_user("UV2@v2", "V2", "v2") is False

    def test_add_user_to_project(self):
        with self.app.app_context():
            assert add_user("V2@V2", "V2", "v2")
            assert add_project("project2", "description")
            assert add_user_to_project(path="project2", access_level='admin', emailid="V2@V2")

    def test_delete_user(self,):
        self.app.app_context().push()
        assert add_user("UV2@v2", "V2", "v2")
        user = User.query.filter_by(emailid="UV2@v2").first()
        assert user is not None
        assert delete_user("UV2@v2")
        user = User.query.filter_by(emailid="UV2@v2").first()
        assert user is None
