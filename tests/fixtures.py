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
import mock

from PyQt5 import QtWidgets, sip
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, initialize_managers
from mslib.mscolab.mscolab import handle_db_init, handle_db_reset
from mslib.utils.config import modify_config_file
from tests.utils import is_url_response_ok, qt_wait_until


# This global keeps the QApplication from getting gc'ed to early. The qapp
# fixture and using this global is inspired by what pytest-qt does as well and
# this global seems to fix some issues with deleted QObject's that came up.
_qapp_instance = None


@pytest.fixture
def qapp():
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        global _qapp_instance
        qapp = _qapp_instance = QtWidgets.QApplication([])

    # Mock every MessageBox widget in the test suite to avoid unwanted freezes on unhandled error popups etc.
    with mock.patch("PyQt5.QtWidgets.QMessageBox.question") as q, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as i, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as c, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.warning") as w:
        yield qapp

        # Fail a test if there are any Qt message boxes left open at the end
        if any(box.call_count > 0 for box in [q, i, c, w]):
            summary = "\n".join([f"PyQt5.QtWidgets.QMessageBox.{box()._extract_mock_name()}: {box.mock_calls[:-1]}"
                                 for box in [q, i, c, w] if box.call_count > 0])
            pytest.fail(f"An unhandled message box popped up during your test!\n{summary}")

    try:
        # Wait until all top level windows and widgets are closed and deleted
        qt_wait_until(
            lambda: len(set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets())) == 0
        )
    except TimeoutError:
        # Not all widgets were closed properly, fail the test and delete all remaining widgets
        widgets = set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets())
        assert len(widgets) == 0, f"There are Qt widgets left open at the end of the test!\n{widgets=}"
        for widget in widgets:
            sip.delete(widget)


@pytest.fixture(scope="session")
def mscolab_session_app():
    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
    handle_db_init()
    return _app


@pytest.fixture
def mscolab_app(mscolab_session_app):
    handle_db_reset()
    return mscolab_session_app


@pytest.fixture(scope="session")
def mscolab_session_managers(mscolab_session_app):
    return initialize_managers(mscolab_session_app)


@pytest.fixture
def mscolab_managers(mscolab_session_managers):
    handle_db_reset()
    return mscolab_session_managers


@pytest.fixture(scope="session")
def mscolab_session_server(mscolab_session_managers):
    app, _, _, _ = mscolab_session_managers
    scheme = "http"
    host = "127.0.0.1"
    server = werkzeug.serving.make_server(host=host, port=0, app=app, threaded=True)
    port = server.socket.getsockname()[1]
    ctx = multiprocessing.get_context("fork")
    process = ctx.Process(target=server.serve_forever, daemon=True)
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
    handle_db_reset()
    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [url]})
    return url, app


@pytest.fixture(scope="session")
def mswms_server():
    scheme = "http"
    host = "127.0.0.1"
    server = werkzeug.serving.make_server(host=host, port=0, app=mslib.mswms.mswms.application, threaded=True)
    port = server.socket.getsockname()[1]
    ctx = multiprocessing.get_context("fork")
    process = ctx.Process(target=server.serve_forever, daemon=True)
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
