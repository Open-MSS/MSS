# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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

import importlib.machinery
import os
import sys
import mock
import warnings
from PyQt5 import QtWidgets
# Disable pyc files
sys.dont_write_bytecode = True

import pytest
import fs
import shutil
from mslib.mswms.demodata import DataFiles
import mslib._tests.constants as constants

# make a copy for mscolab test, so that we read different pathes during parallel tests.
sample_path = os.path.join(os.path.dirname(__file__), "docs", "samples", "flight-tracks")
shutil.copy(os.path.join(sample_path, "example.ftml"), constants.ROOT_DIR)

def pytest_addoption(parser):
    parser.addoption("--msui_settings", action="store")


def pytest_generate_tests(metafunc):
    option_value = metafunc.config.option.msui_settings
    if option_value is not None:
        msui_settings_file_fs = fs.open_fs(constants.MSUI_CONFIG_PATH)
        msui_settings_file_fs.writetext("msui_settings.json", option_value)
        msui_settings_file_fs.close()


if os.getenv("TESTS_VISIBLE") == "TRUE":
    Display = None
else:
    try:
        from pyvirtualdisplay import Display
    except ImportError:
        Display = None

if not constants.SERVER_CONFIG_FS.exists(constants.SERVER_CONFIG_FILE):
    print('\n configure testdata')
    # ToDo check pytest tmpdir_factory
    examples = DataFiles(data_fs=constants.DATA_FS,
                         server_config_fs=constants.SERVER_CONFIG_FS)
    examples.create_server_config(detailed_information=True)
    examples.create_data()

if not constants.SERVER_CONFIG_FS.exists(constants.MSCOLAB_CONFIG_FILE):
    config_string = f'''# -*- coding: utf-8 -*-
"""

    mslib.mscolab.conf.py.example
    ~~~~~~~~~~~~~~~~~~~~

    config for mscolab.

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2022 by the MSS team, see AUTHORS.
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
class mscolab_settings(object):

    # SQLALCHEMY_DB_URI = 'mysql://user:pass@127.0.0.1/mscolab'
    import os
    import logging
    import fs
    import secrets
    from werkzeug.urls import url_join

    ROOT_DIR = '{constants.ROOT_DIR}'
    # directory where mss output files are stored
    root_fs = fs.open_fs(ROOT_DIR)
    if not root_fs.exists('colabTestData'):
        root_fs.makedir('colabTestData')
    BASE_DIR = ROOT_DIR
    DATA_DIR = fs.path.join(ROOT_DIR, 'colabTestData')
    # mscolab data directory
    MSCOLAB_DATA_DIR = fs.path.join(DATA_DIR, 'filedata')

    # used to generate and parse tokens
    SECRET_KEY = secrets.token_urlsafe(16)

    # used to generate the password token
    SECURITY_PASSWORD_SALT = secrets.token_urlsafe(16)

    # mail settings
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # mail authentication
    MAIL_USERNAME = os.environ.get('APP_MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('APP_MAIL_PASSWORD')

    # mail accounts
    MAIL_DEFAULT_SENDER = 'MSS@localhost'

    # enable verification by Mail
    USER_VERIFICATION = False

    SQLALCHEMY_DB_URI = 'sqlite:///' + url_join(DATA_DIR, 'mscolab.db')

    # mscolab file upload settings
    UPLOAD_FOLDER = fs.path.join(DATA_DIR, 'uploads')
    MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

    # text to be written in new mscolab based ftml files.
    STUB_CODE = """<?xml version="1.0" encoding="utf-8"?>
    <FlightTrack version="1.7.6">
      <ListOfWaypoints>
        <Waypoint flightlevel="250" lat="67.821" location="Kiruna" lon="20.336">
          <Comments></Comments>
        </Waypoint>
        <Waypoint flightlevel="250" lat="78.928" location="Ny-Alesund" lon="11.986">
          <Comments></Comments>
        </Waypoint>
      </ListOfWaypoints>
    </FlightTrack>
    """
    enable_basic_http_authentication = False
    '''
    ROOT_FS = fs.open_fs(constants.ROOT_DIR)
    if not ROOT_FS.exists('mscolab'):
        ROOT_FS.makedir('mscolab')
    with fs.open_fs(fs.path.join(constants.ROOT_DIR, "mscolab")) as mscolab_fs:
        # windows needs \\ or / but mixed is terrible. *nix needs /
        mscolab_fs.writetext('mscolab_settings.py', config_string.replace('\\', '/'))
    path = fs.path.join(constants.ROOT_DIR, 'mscolab', 'mscolab_settings.py')
    parent_path = fs.path.join(constants.ROOT_DIR, 'mscolab')


importlib.machinery.SourceFileLoader('mss_wms_settings', constants.SERVER_CONFIG_FILE_PATH).load_module()
sys.path.insert(0, constants.SERVER_CONFIG_FS.root_path)
importlib.machinery.SourceFileLoader('mscolab_settings', path).load_module()
sys.path.insert(0, parent_path)


@pytest.fixture(autouse=True)
def close_open_windows():
    """
    Closes all windows after every test
    """
    # Mock every MessageBox widget in the test suite to avoid unwanted freezes on unhandled error popups etc.
    with mock.patch("PyQt5.QtWidgets.QMessageBox.question") as q, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as i, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as c, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.warning") as w:
        yield
        if any(box.call_count > 0 for box in [q, i, c, w]):
            summary = "\n".join([f"PyQt5.QtWidgets.QMessageBox.{box()._extract_mock_name()}: {box.mock_calls[:-1]}"
                                 for box in [q, i, c, w] if box.call_count > 0])
            warnings.warn(f"An unhandled message box popped up during your test!\n{summary}")


    # Try to close all remaining widgets after each test
    for qobject in set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets()):
        try:
            qobject.destroy()
        # Some objects deny permission, pass in that case
        except RuntimeError:
            pass


@pytest.fixture(scope="session", autouse=True)
def configure_testsetup(request):
    if Display is not None:
        # needs for invisible window output xvfb installed,
        # default backend for visible output is xephyr
        # by visible=0 you get xvfb
        VIRT_DISPLAY = Display(visible=0, size=(1280, 1024))
        VIRT_DISPLAY.start()
        yield
        VIRT_DISPLAY.stop()
    else:
        yield
