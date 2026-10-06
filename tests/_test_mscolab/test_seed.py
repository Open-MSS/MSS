# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_seed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for conf functionalities

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
from pathlib import Path

import git
import pytest
from flask import current_app

from mslib.mscolab.models import User, Operation
from mslib.mscolab.seed import (add_user, get_user, add_operation, add_user_to_operation,
                                delete_user, delete_operation, add_all_users_default_operation, XML_CONTENT_INIT)


class Test_Seed:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        _, _, self.fm = mscolab_managers
        self.operation_name = "XYZ"
        self.description = "Template"
        self.userdata_0 = 'UV0@uv0', 'UV0', 'uv0', 'Usera UV'
        self.userdata_1 = "UV1@uv1", "UV1", "UV1", "Userb UV"
        self.userdata_2 = "UV2@v2", "V2", "v2", "Userc UV"

        with self.app.app_context():
            assert add_user(self.userdata_0[0], self.userdata_0[1], self.userdata_0[2], self.userdata_0[3])
            assert add_operation(self.operation_name, self.description)
            assert add_user_to_operation(path=self.operation_name, emailid=self.userdata_0[0])
            self.user = User(self.userdata_0[0], self.userdata_0[1], self.userdata_0[2])
            yield

    def test_add_operation(self):
        with self.app.test_client():
            assert add_operation("a1", "description")
            operation = Operation.query.filter_by(path="a1").first()
            assert operation.id > 0

    def test_delete_operation(self):
        with self.app.test_client():
            assert add_operation("todelete", "description")
            operation = Operation.query.filter_by(path="todelete").first()
            assert operation.id > 0
            assert delete_operation("todelete")
            operation = Operation.query.filter_by(path="todelete").first()
            assert operation is None

    def test_add_all_users_default_operation_viewer(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2], self.userdata_1[3])
            # viewer
            add_all_users_default_operation(path='XYZ', description="Operation to keep all users",
                                            access_level='viewer')
            expected_result = [{'access_level': 'viewer', 'active': True, 'category': 'default',
                                'description': 'Template', 'op_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            assert user is not None
            result = self.fm.list_operations(user)
            # we don't care here for op_id
            expected_result[0]['op_id'] = result[0]['op_id']
            assert result == expected_result

    def test_add_all_users_default_operation_collaborator(self):
        with self.app.test_client():
            # collaborator
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2], self.userdata_1[3])
            add_all_users_default_operation(path='XYZ', description="Operation to keep all users",
                                            access_level='collaborator')
            expected_result = [{'access_level': 'collaborator', 'active': True, 'category': 'default',
                                'description': 'Template', 'op_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            assert user is not None
            result = self.fm.list_operations(user)
            # we don't care here for op_id
            expected_result[0]['op_id'] = result[0]['op_id']
            assert result == expected_result

    def test_add_all_users_default_operation_creator(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2], self.userdata_1[3])
            # creator
            add_all_users_default_operation(path='XYZ', description="Operation to keep all users",
                                            access_level='creator')
            expected_result = [{'access_level': 'creator', 'active': True, 'category': 'default',
                                'description': 'Template', 'op_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            result = self.fm.list_operations(user)
            # we don't care here for op_id
            expected_result[0]['op_id'] = result[0]['op_id']
            assert result == expected_result

    def test_add_all_users_default_operation_creator_unknown_operation(self):
        with self.app.test_client():
            assert add_user(self.userdata_1[0], self.userdata_1[1], self.userdata_1[2], self.userdata_1[3])
            # creator added to new operation
            add_all_users_default_operation(path='UVXYZ', description="Operation to keep all users",
                                            access_level='creator')
            expected_result = [{'access_level': 'creator', 'active': True, 'category': 'default',
                                'description': 'Operation to keep all users',
                                'op_id': 7, 'path': 'UVXYZ'}]
            user = User.query.filter_by(emailid=self.userdata_1[0]).first()
            result = self.fm.list_operations(user)
            # Check if result is not empty before accessing index
            assert len(result) > 0, f"Expected at least one operation for user {self.userdata_1[0]}, but got empty list"

            # we don't care here for op_id
            expected_result[0]['op_id'] = result[0]['op_id']
            assert result == expected_result

    def test_add_user(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2], self.userdata_2[3])
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2], self.userdata_2[3]) is False

    def test_get_user(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2], self.userdata_2[3])
            user = get_user(self.userdata_2[0])
            assert user.id is not None
            assert user.emailid == self.userdata_2[0]

    def test_add_user_to_operation(self):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2], self.userdata_2[3])
            assert add_operation("operation2", "description")
            assert add_user_to_operation(path="operation2", access_level='admin', emailid=self.userdata_2[0])

    def test_delete_user(self,):
        with self.app.test_client():
            assert add_user(self.userdata_2[0], self.userdata_2[1], self.userdata_2[2], self.userdata_2[3])
            user = User.query.filter_by(emailid=self.userdata_2[0]).first()
            assert user is not None
            assert delete_user(self.userdata_2[0])
            user = User.query.filter_by(emailid=self.userdata_2[0]).first()
            assert user is None


@pytest.mark.parametrize("leftover", ["empty", "main.ftml"])
def test_add_operation_creates_missing_files(mscolab_app, leftover):
    """A directory left over without main.ftml or git repository, e.g. by an interrupted reset"""
    with mscolab_app.app_context():
        operation_dir = Path(current_app.config['OPERATIONS_DATA']) / "leftover"
        operation_dir.mkdir(parents=True)
        if leftover == "main.ftml":
            (operation_dir / "main.ftml").write_text("not a flight track")
        assert add_operation("leftover", "description")
        assert (operation_dir / "main.ftml").read_text(encoding="utf-8") == XML_CONTENT_INIT
        with git.Repo(operation_dir) as repo:
            assert repo.head.commit.message == "initial commit"
            assert not repo.is_dirty()


def test_add_operation_keeps_existing_files(mscolab_app):
    with mscolab_app.app_context():
        operation_dir = Path(current_app.config['OPERATIONS_DATA']) / "existing"
        assert add_operation("existing", "description")
        (operation_dir / "main.ftml").write_text("changed", encoding="utf-8")
        assert delete_operation("existing")
        assert add_operation("existing", "description")
        assert (operation_dir / "main.ftml").read_text(encoding="utf-8") == "changed"
