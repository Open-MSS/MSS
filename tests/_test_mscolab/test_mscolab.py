# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab functionalities

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2025 by the MSS team, see AUTHORS.
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

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Operation, User, Permission
from mslib.mscolab.mscolab import handle_db_reset, handle_db_seed, confirm_action, main
from mslib.mscolab.seed import add_operation


def test_version_argument(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["mscolab.py", "--version"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Version:" in captured.out


def test_start_argument(monkeypatch, caplog):
    mock_setup_logging_called = []
    mock_start_server_called = []

    def mock_setup_logging(args):
        mock_setup_logging_called.append(args)

    def mock_start_server(app, sockio, cm, fm):
        mock_start_server_called.append((app, sockio, cm, fm))

    monkeypatch.setattr("mslib.mscolab.mscolab.setup_logging", mock_setup_logging)
    monkeypatch.setattr("mslib.mscolab.server.start_server", mock_start_server)
    monkeypatch.setattr("sys.argv", ["mscolab.py", "start"])

    main()
    assert len(mock_setup_logging_called) == 1
    assert len(mock_start_server_called) == 1
    assert "Launching MSColab Server" in caplog.text


@pytest.mark.parametrize("confirmation_input, expected_result", [
    (["y"], True),
    (["n"], False),
    (["invalid", "y"], True),
])
def test_confirm_action(monkeypatch, confirmation_input, expected_result):
    input_generator = iter(confirmation_input)
    monkeypatch.setattr("builtins.input", lambda _: next(input_generator))
    result = confirm_action("Are you sure?")
    assert result == expected_result


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
        assert os.path.isdir(mscolab_settings.OPERATIONS_DATA)
        all_operations = Operation.query.all()
        assert all_operations == []
        operation_name = "Example"
        assert add_operation(operation_name, "Test Example")
        assert os.path.isdir(os.path.join(mscolab_settings.OPERATIONS_DATA, operation_name))
        operation = Operation.query.filter_by(path=operation_name).first()
        assert operation.description == "Test Example"
        all_operations = Operation.query.all()
        assert len(all_operations) == 1
        handle_db_reset()
        # check operation dir name removed
        assert os.path.isdir(os.path.join(mscolab_settings.OPERATIONS_DATA, operation_name)) is False
        assert os.path.isdir(mscolab_settings.OPERATIONS_DATA)
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
