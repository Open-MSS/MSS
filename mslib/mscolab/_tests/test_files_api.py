# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_files_api
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    api integration tests for file based handlers

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
import os
import fs
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Project, db
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.mscolab import handle_db_seed


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Files(object):
    def setup(self):
        handle_db_seed()
        self.app = Flask(__name__, static_url_path='')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.user = get_user(self.userdata[0])
        assert self.user is not None
        assert add_user('UV20@uv20', 'UV20', 'uv20')
        self.user_2 = get_user('UV20@uv20')

    def teardown(self):
        pass

    def test_create_project(self):
        with self.app.app_context():
            flight_path = "f3"
            project = Project.query.filter_by(path=flight_path).first()
            assert project is None
            assert self.fm.create_project(flight_path, "f3 test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            assert project.id is not None
            assert project.path == "f3"

    def test_list_projects(self):
        with self.app.app_context():
            projects = ["alpha", "beta", "gamma"]
            for fp in projects:
                assert self.fm.create_project(fp, f"{fp} test example", self.user)
            assert len(self.fm.list_projects(self.user)) == 3
            assert len(self.fm.list_projects(self.user_2)) == 0
            fps = self.fm.list_projects(self.user)
            all_projects = [fp['path'] for fp in fps]
            assert projects == all_projects

    def test_get_project_details(self):
        with self.app.app_context():
            flight_path = "V1"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            details = self.fm.get_project_details(project.id, self.user)
            assert details["description"] == f"{flight_path} test example"
            assert details["path"] == flight_path
            assert details["id"] == project.id

    def test_get_authorized_users(self):
        with self.app.app_context():
            flight_path = "V1"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            users = self.fm.get_authorized_users(project.id)
            assert users[0] == {'username': 'UV10', 'access_level': 'creator'}

    def test_fetch_users_without_permission(self):
        with self.app.app_context():
            flight_path = "V2"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            assert self.fm.fetch_users_without_permission(project.id, self.user_2.id) is False
            without_permission = self.fm.fetch_users_without_permission(project.id, self.user.id)
            # ToDo after seeding removed use absolut comparison
            assert without_permission[-1] == [self.user_2.username, self.user_2.id]

    def test_fetch_users_with_permission(self):
        with self.app.app_context():
            flight_path = "V3"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            assert self.fm.fetch_users_with_permission(project.id, self.user_2.id) is False
            # we look in the query only on others than creator
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == []

    def test_add_bulk_permissions(self):
        with self.app.app_context():
            flight_path = "V4"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(project.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]

    def test_modify_bulk_permissions(self):
        with self.app.app_context():
            flight_path = "V5"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(project.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]
            self.fm.modify_bulk_permission(project.id, self.user, [self.user_2.id], "collaborator")
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'collaborator', self.user_2.id]]

    def test_delete_bulk_permissions(self):
        with self.app.app_context():
            flight_path = "V6"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(project.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]
            assert self.fm.delete_bulk_permission(project.id, self.user, [self.user_2.id])
            with_permission = self.fm.fetch_users_with_permission(project.id, self.user.id)
            assert with_permission == []

    def test_import_permissions(self):
        with self.app.app_context():
            flight_path = "V7"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project_1 = Project.query.filter_by(path=flight_path).first()
            with_permission = self.fm.fetch_users_with_permission(project_1.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(project_1.id, self.user, [self.user_2.id], "viewer")

            flight_path = "V8"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project_2 = Project.query.filter_by(path=flight_path).first()
            with_permission = self.fm.fetch_users_with_permission(project_2.id, self.user.id)
            assert with_permission == []

            self.fm.import_permissions(project_1.id, project_2.id, self.user.id)
            with_permission = self.fm.fetch_users_with_permission(project_2.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]

    def test_update_project(self):
        with self.app.app_context():
            flight_path = "V9"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            new_flight_path = 'NEW_V9'
            assert self.fm.update_project(project.id, 'path', new_flight_path, self.user)
            project = Project.query.filter_by(path=new_flight_path).first()
            assert project.path == new_flight_path
            data = fs.open_fs(self.fm.data_dir)
            assert data.exists(new_flight_path)
            new_description = "my new description"
            assert self.fm.update_project(project.id, 'description', new_description, self.user)
            project = Project.query.filter_by(path=new_flight_path).first()
            assert project.description == new_description

    def test_delete_file(self):
        # ToDo rename to project
        with self.app.app_context():
            flight_path = "V10"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            assert project.path == flight_path
            assert self.fm.delete_file(project.id, self.user)
            project = Project.query.filter_by(path=flight_path).first()
            assert project is None

    def test_get_all_changes(self):
        with self.app.app_context():
            flight_path = "V11"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user, content='initial')
            project = Project.query.filter_by(path=flight_path).first()
            assert self.fm.save_file(project.id, "content1", self.user)
            assert self.fm.save_file(project.id, "content2", self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert len(all_changes) == 2

    def test_get_change_content(self):
        with self.app.app_context():
            flight_path = "V12"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user, content='initial')
            project = Project.query.filter_by(path=flight_path).first()
            assert self.fm.save_file(project.id, "content1", self.user)
            assert self.fm.save_file(project.id, "content2", self.user)
            assert self.fm.save_file(project.id, "content3", self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            previous_change = self.fm.get_change_content(all_changes[2]["id"])
            assert previous_change == "content1"
            previous_change = self.fm.get_change_content(all_changes[1]["id"])
            assert previous_change == "content2"

    def test_set_version_name(self):
        with self.app.app_context():
            flight_path = "V13"
            assert self.fm.create_project(flight_path, f"{flight_path} test example", self.user, content='initial')
            project = Project.query.filter_by(path=flight_path).first()
            assert self.fm.save_file(project.id, "content1", self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            ch_id = all_changes[-1]["id"]
            self.fm.set_version_name(ch_id, project.id, self.user.id, "berlin")
            all_changes = self.fm.get_all_changes(project.id, self.user)
            version_name = all_changes[-1]["version_name"]
            assert version_name == "berlin"
