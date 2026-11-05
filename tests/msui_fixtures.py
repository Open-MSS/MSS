# -*- coding: utf-8 -*-
"""

    tests.msui_fixtures
    ~~~~~~~~~~~~~~~~~~~

    Fixtures of the desktop client's test suites: the test keyring, the reset of the msui configuration and the
    Qt helpers. The conftest.py of tests/_test_msui and tests/_test_plugins load them; the suites of the servers
    and of mslib.utils run without msui, keyring and PyQt5 installed.

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import keyring
import mock
import pytest
from PyQt5 import QtWidgets

# tests.constants sets MSUI_CONFIG_PATH, which mslib.msui.utils.config needs at import time
from tests.constants import create_msui_settings_file
from mslib.msui.utils.config import modify_config_file, read_config_file


class TestKeyring(keyring.backend.KeyringBackend):
    """A test keyring which always outputs the same password
    from Runtime Configuration
    https://pypi.org/project/keyring/#third-party-backends
    """
    priority = 1

    passwords = {}

    def reset(self):
        self.passwords = {}

    def set_password(self, servicename, username, password):
        self.passwords[servicename + username] = password

    def get_password(self, servicename, username):
        return self.passwords.get(servicename + username, "password from TestKeyring")

    def delete_password(self, servicename, username):
        if servicename + username in self.passwords:
            del self.passwords[servicename + username]


# set the keyring for keyring lib
keyring.set_keyring(TestKeyring())


@pytest.fixture(autouse=True)
def keyring_reset():
    keyring.get_keyring().reset()


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the msui configuration file used in the tests after every test."""
    create_msui_settings_file("{}")
    read_config_file()


@pytest.fixture
def fail_if_open_message_boxes_left():
    # Mock every MessageBox widget in the test suite to avoid unwanted freezes on unhandled error popups etc.
    with mock.patch("PyQt5.QtWidgets.QMessageBox.question") as q, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as i, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as c, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.warning") as w:
        yield

        # Fail a test if there are any Qt message boxes left open at the end
        if any(box.call_count > 0 for box in [q, i, c, w]):
            summary = "\n".join([f"PyQt5.QtWidgets.QMessageBox.{box()._extract_mock_name()}: {box.mock_calls[:-1]}"
                                 for box in [q, i, c, w] if box.call_count > 0])
            pytest.fail(f"An unhandled message box popped up during your test!\n{summary}")


@pytest.fixture
def mscolab_server(mscolab_server):
    """The mscolab_server fixture of tests/fixtures.py, with its URL in the msui configuration

    so that msui shows no "Update Server List" message box for it.
    """
    modify_config_file({"default_MSCOLAB": [mscolab_server]})
    return mscolab_server


@pytest.fixture
def msui_configs(tmp_path):
    modify_config_file({"mscolab_local_data_dir": str(tmp_path)})


@pytest.fixture
def qtbot(qtbot, fail_if_open_message_boxes_left, msui_configs):
    """Fixture that re-defines the qtbot fixture from pytest-qt with additional checks."""
    yield qtbot
    # Drop any matplotlib figures from Gcf BEFORE scheduling Qt deletion, otherwise
    # matplotlib's atexit Gcf.destroy_all trips over a dead NavigationToolbar2QT at
    # worker shutdown ("wrapped C/C++ object has been deleted").
    try:
        import matplotlib.pyplot as plt
        plt.close("all")
    except ImportError:
        pass
    # Schedule destruction of any leftover top-level widgets BEFORE the drain wait
    # below. Tests often only call hide(), which keeps the widget (and any sockets
    # it owns) alive. deleteLater() queues destruction without firing close events
    # (close() would trigger "save changes?" dialogs); the subsequent qtbot.wait
    # gives the Qt event loop time to actually process the deletions.
    for qobject in set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets()):
        try:
            delete_later = getattr(qobject, "deleteLater", None)
            if delete_later is not None:
                delete_later()
        # Some objects are already deleted; ignore those.
        except RuntimeError:
            pass
    # Drain the Qt event loop so destruction (and any socket disconnects it triggers)
    # actually completes before the next test starts.
    qtbot.wait(5000)
