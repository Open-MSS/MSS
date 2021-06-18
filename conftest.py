# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

import importlib
import importlib.machinery
import os
import sys
# Disable pyc files
sys.dont_write_bytecode = True

import pytest
import fs
from mslib.mswms.demodata import DataFiles
import mslib._tests.constants as constants


def pytest_addoption(parser):
    parser.addoption("--mss_settings", action="store")


def pytest_generate_tests(metafunc):
    option_value = metafunc.config.option.mss_settings
    if option_value is not None:
        mss_settings_file_fs = fs.open_fs(constants.MSS_CONFIG_PATH)
        mss_settings_file_fs.writetext("mss_settings.json", option_value)
        mss_settings_file_fs.close()


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
