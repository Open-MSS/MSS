# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_files_api
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    api integration tests for file based handlers

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import time
import fs
import pytest

from mslib.mscolab.models import Operation
from mslib.mscolab.seed import add_user, get_user


class Test_Files():
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        _, _, self.fm = mscolab_managers
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.user = get_user(self.userdata[0])
        assert self.user is not None
        assert add_user('UV20@uv20', 'UV20', 'uv20')
        self.user_2 = get_user('UV20@uv20')
        with self.app.app_context():
            yield

    def test_create_operation(self):
        with self.app.test_client():
            flight_path = "f3"
            operation = Operation.query.filter_by(path=flight_path).first()
            assert operation is None
            assert self.fm.create_operation(flight_path, "f3 test example", self.user)
            operation = Operation.query.filter_by(path=flight_path).first()
            assert operation.id is not None
            assert operation.path == "f3"

    def test_list_operations(self):
        with self.app.test_client():
            operations = ["alpha", "beta", "gamma"]
            for fp in operations:
                assert self.fm.create_operation(fp, f"{fp} test example", self.user)
            assert len(self.fm.list_operations(self.user)) == 3
            assert len(self.fm.list_operations(self.user_2)) == 0
            fps = self.fm.list_operations(self.user)
            all_operations = [fp['path'] for fp in fps]
            assert operations == all_operations

    def test_get_operation_details(self):
        with self.app.test_client():
            description = "test example"
            flight_path, operation = self._create_operation(flight_path="V1", description=description)
            details = self.fm.get_operation_details(operation.id, self.user)
            assert details["description"] == description
            assert details["path"] == flight_path
            assert details["id"] == operation.id

    def test_get_authorized_users(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V1")
            users = self.fm.get_authorized_users(operation.id)
            assert users[0] == {'username': 'UV10', 'access_level': 'creator'}

    def test_fetch_users_without_permission(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V2")
            assert self.fm.fetch_users_without_permission(operation.id, self.user_2.id) is False
            without_permission = self.fm.fetch_users_without_permission(operation.id, self.user.id)
            # ToDo after seeding removed use absolut comparison
            assert without_permission[-1] == [self.user_2.username, self.user_2.id]

    def test_fetch_users_with_permission(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V3")
            assert self.fm.fetch_users_with_permission(operation.id, self.user_2.id) is False
            # we look in the query only on others than creator
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == []

    def test_add_bulk_permissions(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V4")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(operation.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]

    def test_modify_bulk_permissions(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V5")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(operation.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]
            self.fm.modify_bulk_permission(operation.id, self.user, [self.user_2.id], "collaborator")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'collaborator', self.user_2.id]]

    def test_delete_bulk_permissions(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V6")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(operation.id, self.user, [self.user_2.id], "viewer")
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]
            assert self.fm.delete_bulk_permission(operation.id, self.user, [self.user_2.id])
            with_permission = self.fm.fetch_users_with_permission(operation.id, self.user.id)
            assert with_permission == []

    def test_import_permissions(self):
        with self.app.test_client():
            flight_path, operation_1 = self._create_operation(flight_path="V7")
            with_permission = self.fm.fetch_users_with_permission(operation_1.id, self.user.id)
            assert with_permission == []
            self.fm.add_bulk_permission(operation_1.id, self.user, [self.user_2.id], "viewer")

            flight_path, operation_2 = self._create_operation(flight_path="V8")
            with_permission = self.fm.fetch_users_with_permission(operation_2.id, self.user.id)
            assert with_permission == []

            self.fm.import_permissions(operation_1.id, operation_2.id, self.user.id)
            with_permission = self.fm.fetch_users_with_permission(operation_2.id, self.user.id)
            assert with_permission == [[self.user_2.username, 'viewer', self.user_2.id]]

    def test_update_operation(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V9")
            new_flight_path = 'NEW_V9'
            assert self.fm.update_operation(operation.id, 'path', new_flight_path, self.user)
            operation = Operation.query.filter_by(path=new_flight_path).first()
            assert operation.path == new_flight_path
            data = fs.open_fs(self.fm.data_dir)
            assert data.exists(new_flight_path)
            new_description = "my new description"
            assert self.fm.update_operation(operation.id, 'description', new_description, self.user)
            operation = Operation.query.filter_by(path=new_flight_path).first()
            assert operation.description == new_description

    def test_delete_operation(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V10")
            assert operation.path == flight_path
            assert self.fm.delete_operation(operation.id, self.user)
            operation = Operation.query.filter_by(path=flight_path).first()
            assert operation is None

    def test_get_all_changes(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V11")
            assert self.fm.save_file(operation.id, "content1", self.user)
            # we need to wait to get an updated created_at
            time.sleep(1)
            assert self.fm.save_file(operation.id, "content2", self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            # the newest change is on index 0, because it has a recent created_at time
            assert len(all_changes) == 2
            assert all_changes[0]["id"] == 2
            assert all_changes[0]["id"] > all_changes[1]["id"]
            assert all_changes[0]["created_at"] > all_changes[1]["created_at"]

    def test_get_change_content(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V12", content='initial')
            assert self.fm.save_file(operation.id, "content1", self.user)
            assert self.fm.save_file(operation.id, "content2", self.user)
            assert self.fm.save_file(operation.id, "content3", self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            previous_change = self.fm.get_change_content(all_changes[2]["id"], self.user)
            assert previous_change == "content1"
            previous_change = self.fm.get_change_content(all_changes[1]["id"], self.user)
            assert previous_change == "content2"

    def test_set_version_name(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="V13", content='initial')
            assert self.fm.save_file(operation.id, "content1", self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            ch_id = all_changes[-1]["id"]
            self.fm.set_version_name(ch_id, operation.id, self.user.id, "berlin")
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            version_name = all_changes[-1]["version_name"]
            assert version_name == "berlin"

    def _create_operation(self, flight_path="firstflight", description="example", user=None, content=None):
        if user is None:
            user = self.user
        self.fm.create_operation(flight_path, description, user, content=content)
        operation = Operation.query.filter_by(path=flight_path).first()
        return flight_path, operation
 