# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab functionalities

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import os
import pytest
import mock
import argparse

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Operation, User, Permission
from mslib.mscolab.mscolab import handle_db_reset, handle_db_seed, confirm_action, main
from mslib.mscolab.seed import add_operation


def test_confirm_action():
    with mock.patch("mslib.mscolab.mscolab.input", return_value="n"):
        assert confirm_action("") is False
    with mock.patch("mslib.mscolab.mscolab.input", return_value=""):
        assert confirm_action("") is False
    with mock.patch("mslib.mscolab.mscolab.input", return_value="y"):
        assert confirm_action("") is True


def test_main():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        with mock.patch("mslib.mscolab.mscolab.argparse.ArgumentParser.parse_args",
                        return_value=argparse.Namespace(version=True)):
            main()
        assert pytest_wrapped_e.typename == "SystemExit"

    with mock.patch("mslib.mscolab.mscolab.argparse.ArgumentParser.parse_args",
                    return_value=argparse.Namespace(version=False, update=False, action="db",
                                                    reset=False, seed=False, users_by_file=None,
                                                    default_operation=False, add_all_to_all_operation=False,
                                                    delete_users_by_file=False)):
        main()
        # currently only checking precedence of all args


class Test_Mscolab:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app):
        with mscolab_app.app_context():
            yield

    def test_initial_state(self):
        assert Operation.query.all() == []
        assert User.query.all() == []
        assert Permission.query.all() == []

    def test_handle_db_reset(self):
        assert os.path.isdir(mscolab_settings.UPLOAD_FOLDER)
        assert os.path.isdir(mscolab_settings.FILE_DATA)
        all_operations = Operation.query.all()
        assert all_operations == []
        operation_name = "Example"
        assert add_operation(operation_name, "Test Example")
        assert os.path.isdir(os.path.join(mscolab_settings.FILE_DATA, operation_name))
        operation = Operation.query.filter_by(path=operation_name).first()
        assert operation.description == "Test Example"
        all_operations = Operation.query.all()
        assert len(all_operations) == 1
        handle_db_reset()
        # check operation dir name removed
        assert os.path.isdir(os.path.join(mscolab_settings.FILE_DATA, operation_name)) is False
        assert os.path.isdir(mscolab_settings.FILE_DATA)
        assert os.path.isdir(mscolab_settings.UPLOAD_FOLDER)
        # query db for operation_name
        operation = Operation.query.filter_by(path=operation_name).first()
        assert operation is None
        all_operations = Operation.query.all()
        assert all_operations == []

    def test_handle_db_seed(self):
        all_operations = Operation.query.all()
        assert all_operations == []
        handle_db_seed()
        all_operations = Operation.query.all()
        assert len(all_operations) == 6
        assert all_operations[0].path == "one"
        all_users = User.query.all()
        assert len(all_users) == 10
        all_permissions = Permission.query.all()
        assert len(all_permissions) == 17
