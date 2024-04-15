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
import pytest
import mock
import multiprocessing
import time
import urllib
import mslib.mswms.mswms
import eventlet
import eventlet.wsgi

from PyQt5 import QtWidgets
from contextlib import contextmanager
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, initialize_managers
from mslib.mscolab.mscolab import handle_db_init, handle_db_reset
from mslib.utils.config import modify_config_file
from tests.utils import is_url_response_ok


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
def close_remaining_widgets():
    yield
    # Try to close all remaining widgets after each test
    for qobject in set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets()):
        try:
            qobject.destroy()
        # Some objects deny permission, pass in that case
        except RuntimeError:
            pass


@pytest.fixture
def qtbot(qtbot, fail_if_open_message_boxes_left, close_remaining_widgets):
    """Fixture that re-defines the qtbot fixture from pytest-qt with additional checks."""
    yield qtbot
    # Wait for a while after the requesting test has finished. At time of writing this
    # is required to (mostly) stabilize the coverage reports, because tests don't
    # properly close their Qt-related stuff and therefore there is no guarantee about
    # what the Qt event loop has or hasn't done yet. Waiting just gives it a bit more
    # time to converge on the same result every time the tests are executed. This is a
    # band-aid fix, the proper fix is to make sure each test cleans up after itself.
    qtbot.wait(5000)


@pytest.fixture(scope="session")
def mscolab_session_app():
    """Session-scoped fixture that provides the WSGI app instance for MSColab.

    This fixture should not be used in tests. Instead use :func:`mscolab_app`, which
    handles per-test cleanup as well.
    """
    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
    handle_db_init()
    return _app


@pytest.fixture(scope="session")
def mscolab_session_managers(mscolab_session_app):
    """Session-scoped fixture that provides the managers for the MSColab app.

    This fixture should not be used in tests. Instead use :func:`mscolab_managers`,
    which handles per-test cleanup as well.
    """
    return initialize_managers(mscolab_session_app)[1:]


@pytest.fixture(scope="session")
def mscolab_session_server(mscolab_session_app, mscolab_session_managers):
    """Session-scoped fixture that provides a running MSColab server.

    This fixture should not be used in tests. Instead use :func:`mscolab_server`, which
    handles per-test cleanup as well.
    """
    with _running_eventlet_server(mscolab_session_app) as url:
        yield url


@pytest.fixture
def reset_mscolab(mscolab_session_app):
    """Cleans up before every test that uses MSColab.

    This fixture is not explicitly needed in tests, it is used in the other fixtures to
    do the cleanup actions.
    """
    handle_db_reset()


@pytest.fixture
def mscolab_app(mscolab_session_app, reset_mscolab):
    """Fixture that provides the MSColab WSGI app instance and does cleanup actions.

    :returns: A WSGI app instance.
    """
    return mscolab_session_app


@pytest.fixture
def mscolab_managers(mscolab_session_managers, reset_mscolab):
    """Fixture that provides the MSColab managers and does cleanup actions.

    :returns: A tuple (SocketIO, ChatManager, FileManager) as returned by
        initialize_managers.
    """
    return mscolab_session_managers


@pytest.fixture
def mscolab_server(mscolab_session_server, reset_mscolab):
    """Fixture that provides a running MSColab server and does cleanup actions.

    :returns: The URL where the server is running.
    """
    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [mscolab_session_server]})
    return mscolab_session_server


@pytest.fixture(scope="session")
def mswms_app():
    """Fixture that provides the MSWMS WSGI app instance."""
    return mslib.mswms.mswms.application


@pytest.fixture(scope="session")
def mswms_server(mswms_app):
    """Fixture that provides a running MSWMS server.

    :returns: The URL where the server is running.
    """
    with _running_eventlet_server(mswms_app) as url:
        yield url


@contextmanager
def _running_eventlet_server(app):
    """Context manager that starts the app in an eventlet server and returns its URL."""
    scheme = "http"
    host = "127.0.0.1"
    socket = eventlet.listen((host, 0))
    port = socket.getsockname()[1]
    url = f"{scheme}://{host}:{port}"
    app.config['URL'] = url
    if "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("requires the multiprocessing start_method 'fork', which is unavailable on this system")
    ctx = multiprocessing.get_context("fork")
    process = ctx.Process(target=eventlet.wsgi.server, args=(socket, app), daemon=True)
    try:
        process.start()
        while not is_url_response_ok(urllib.parse.urljoin(url, "index")):
            time.sleep(0.5)
        yield url
    finally:
        process.terminate()
        process.join(10)
        process.close()
