# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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
from __future__ import print_function


import imp
import os
import sys
import socket
# Disable pyc files
sys.dont_write_bytecode = True

import multiprocessing
import time
import pytest
import fs
from mslib.mswms.demodata import DataFiles
import mslib._tests.constants as constants

PORTS = list(range(9300, 9600))


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
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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

    ROOT_DIR = '{constants.ROOT_DIR}'
    # directory where mss output files are stored
    root_fs = fs.open_fs(ROOT_DIR)
    if not root_fs.exists('colabTestData'):
        root_fs.makedir('colabTestData')
    BASE_DIR = ROOT_DIR
    DATA_DIR = os.path.join(ROOT_DIR, 'colabTestData')
    # mscolab data directory
    MSCOLAB_DATA_DIR = os.path.join(DATA_DIR, 'filedata')

    # used to generate and parse tokens
    SECRET_KEY = secrets.token_urlsafe(16)

    SQLALCHEMY_DB_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'mscolab.db')

    # mscolab file upload settings
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
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
    with fs.open_fs(os.path.join(constants.ROOT_DIR, "mscolab")) as mscolab_fs:
        mscolab_fs.writetext('mscolab_settings.py', config_string)
    path = os.path.join(constants.ROOT_DIR, 'mscolab', 'mscolab_settings.py')
    parent_path = os.path.join(constants.ROOT_DIR, 'mscolab')


imp.load_source('mss_wms_settings', constants.SERVER_CONFIG_FILE_PATH)
sys.path.insert(0, constants.SERVER_CONFIG_FS.root_path)
imp.load_source('mscolab_settings', path)
sys.path.insert(0, parent_path)

# ToDo scope="class" for mscolab tests wanted

@pytest.fixture(scope="session")
def create_data():
    from mslib.mscolab.mscolab import handle_db_seed
    handle_db_seed()
    yield
    constants.ROOT_FS.clean()


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


process = None


def check_free_port(port):
    _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _s.bind(("127.0.0.1", port))
    except socket.error:
        port = PORTS.pop()
        check_free_port(port)
    _s.close()
    return port


@pytest.fixture(scope="class")
def start_mscolab_server(request):
    testname = request.node.name
    port = check_free_port(PORTS.pop() + len(testname))
    from mslib.mscolab.conf import mscolab_settings
    from mslib.mscolab.server import APP, initialize_managers, start_server
    url = f"http://localhost:{port}"

    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
    _app.config['URL'] = url

    _app, sockio, cm, fm = initialize_managers(_app)
    global process
    process = multiprocessing.Process(
        target=start_server,
        args=(_app, sockio, cm, fm,),
        kwargs={'port': port})
    process.start()
    time.sleep(2)


@pytest.fixture(scope="session")
def stop_server(request):
    """Cleanup a testing directory once we are finished."""
    def stop_callback():
        global process
        process.terminate()
    request.addfinalizer(stop_callback)


@pytest.fixture(scope="class")
def testdata_exists():
    if not constants.ROOT_FS.exists(u'mss'):
        pytest.skip("testdata not existing")


assert sys.path[0].startswith('/tmp')
