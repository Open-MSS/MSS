# -*- coding: utf-8 -*-
"""

    tests.fixtures
    ~~~~~~~~~~~~~~

    This module provides utils for pytest to test mslib modules

    This file is part of MSS.

    :copyright: Copyright 2023 by the MSS team, see AUTHORS.
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
import multiprocessing
import werkzeug
import pytest
import time
import urllib
import mslib.mswms.mswms

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, initialize_managers
from mslib.mscolab.mscolab import handle_db_init
from mslib.utils.config import modify_config_file
from tests.utils import is_url_response_ok


@pytest.fixture(scope="session")
def mscolab_app():
    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
    return _app


@pytest.fixture(scope="session")
def mscolab_managers(mscolab_app):
    return initialize_managers(mscolab_app)


@pytest.fixture(scope="session")
def mscolab_session_server(mscolab_managers):
    handle_db_init()
    app, _, _, _ = mscolab_managers
    scheme = "http"
    host = "127.0.0.1"
    server = werkzeug.serving.make_server(host=host, port=0, app=app, threaded=True)
    port = server.socket.getsockname()[1]
    process = multiprocessing.Process(target=server.serve_forever, daemon=True)
    process.start()
    url = f"{scheme}://{host}:{port}"
    app.config['URL'] = url
    while not is_url_response_ok(urllib.parse.urljoin(url, "index")):
        time.sleep(0.5)
    try:
        yield url, app
    finally:
        process.terminate()
        process.join(10)
        process.close()


@pytest.fixture
def mscolab_server(mscolab_session_server):
    url, app = mscolab_session_server
    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [url]})
    return url, app


@pytest.fixture(scope="session")
def mswms_server():
    scheme = "http"
    host = "127.0.0.1"
    server = werkzeug.serving.make_server(host=host, port=0, app=mslib.mswms.mswms.application, threaded=True)
    port = server.socket.getsockname()[1]
    process = multiprocessing.Process(target=server.serve_forever, daemon=True)
    process.start()
    url = f"{scheme}://{host}:{port}"
    while not is_url_response_ok(urllib.parse.urljoin(url, "index")):
        time.sleep(0.5)
    try:
        yield url
    finally:
        process.terminate()
        process.join(10)
        process.close()
