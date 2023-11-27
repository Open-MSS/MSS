# -*- coding: utf-8 -*-
"""

    tests.utils
    ~~~~~~~~~~~

    This module provides utils for pytest to test mslib modules

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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
import time
import fs
import sys
import re
import socket
import multiprocessing

from flask_testing import LiveServerTestCase

from contextlib import contextmanager
from urllib.parse import urljoin
from mslib.mscolab.server import register_user
from flask import json
from tests.constants import MSUI_CONFIG_PATH
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import APP, initialize_managers, start_server
from mslib.mscolab.mscolab import handle_db_init
from mslib.utils.config import modify_config_file


def callback_ok_image(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'image/png')


def callback_ok_xml(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'text/xml')


def callback_ok_html(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-Type', 'text/html; charset=utf-8')


def callback_404_plain(status, response_headers):
    assert status == "404 NOT FOUND"
    assert response_headers[0] == ('Content-type', 'text/plain')


def callback_307_html(status, response_headers):
    assert status == "307 TEMPORARY REDIRECT"
    assert response_headers[0] == ('Content-Type', 'text/html; charset=utf-8')


def mscolab_register_user(app, msc_url, email, password, username):
    # Duplicate of imported register_user
    data = {
        'email': email,
        'password': password,
        'username': username
    }
    url = urljoin(msc_url, 'register')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_register_and_login(app, msc_url, email, password, username):
    register_user(email, password, username)
    data = {
        'email': email,
        'password': password
    }
    url = urljoin(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_login(app, msc_url, email='a', password='a'):
    data = {
        'email': email,
        'password': password
    }
    url = urljoin(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_user(app, msc_url, email, password):
    with app.app_context():
        response = mscolab_login(app, msc_url, email, password)
        if response.status == '200 OK':
            data = json.loads(response.get_data(as_text=True))
            url = urljoin(msc_url, 'delete_own_account')
            response = app.test_client().post(url, data=data)
            if response.status == '200 OK':
                data = json.loads(response.get_data(as_text=True))
                return data["success"]
        return False


def mscolab_create_content(app, msc_url, data, path_name='example', content=None):
    if content is None:
        content = f"""\
        <?xml version="1.0" encoding="utf-8"?>
          <FlightTrack>
            <Name>{path_name}</Name>
            <ListOfWaypoints>
              <Waypoint flightlevel="0.0" lat="55.15" location="A1" lon="-23.74">
                <Comments>Takeoff</Comments>
              </Waypoint>
              <Waypoint flightlevel="350" lat="42.99" location="A2" lon="-12.1">
                <Comments></Comments>
              </Waypoint>
              </ListOfWaypoints>
          </FlightTrack>"""
    data["path"] = path_name
    data['description'] = path_name
    data['content'] = content
    url = urljoin(msc_url, 'create_operation')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_all_operations(app, msc_url, email, password, username):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = urljoin(msc_url, 'operations')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['operations']:
        data['op_id'] = p['op_id']
        url = urljoin(msc_url, 'delete_operation')
        response = app.test_client().post(url, data=data)


def mscolab_create_operation(app, msc_url, response, path='f', description='description'):
    data = json.loads(response.get_data(as_text=True))
    data["path"] = path
    data['description'] = description
    url = urljoin(msc_url, 'create_operation')
    response = app.test_client().post(url, data=data)
    return data, response


def mscolab_get_operation_id(app, msc_url, email, password, username, path):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = urljoin(msc_url, 'operations')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['operations']:
        if p['path'] == path:
            return p['op_id']


def mscolab_check_free_port(all_ports, port):
    _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _s.bind(("127.0.0.1", port))
    except (socket.error, IOError):
        port = all_ports.pop()
        port = mscolab_check_free_port(all_ports, port)
    else:
        _s.close()
    return port


@contextmanager
def capture_stderr():
    class TeeToPipe:
        def __init__(self, wrapped, pipe):
            self.wrapped = wrapped
            self.pipe = pipe

        def write(self, data):
            self.pipe.send(data)
            self.wrapped.write(data)

    rd, w = multiprocessing.Pipe(duplex=False)
    stderr = sys.stderr
    sys.stderr = TeeToPipe(stderr, w)
    try:
        yield rd
    finally:
        sys.stderr = stderr
        rd.close()
        w.close()


def mscolab_start_server():
    handle_db_init()

    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
    _app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
    _app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER

    _app, sockio, cm, fm = initialize_managers(_app)

    # ToDo refactoring for spawn needed, fork is not implemented on windows, spawn is default on MAC and Windows
    if multiprocessing.get_start_method(allow_none=True) != 'fork':
        multiprocessing.set_start_method("fork")
    with capture_stderr() as stderr:
        process = multiprocessing.Process(
            target=start_server,
            args=(_app, sockio, cm, fm,),
            kwargs={"port": 0, "log_output": True})
        process.start()

        while True:
            out = stderr.recv()
            m = re.match(r"^\(\d+\) wsgi starting up on (https?)://([^:]+):(\d+)$", out)
            if m is not None:
                scheme, host, port = m.groups()
                break

    url = f"{scheme}://{host}:{port}"
    _app.config['URL'] = url

    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [url]})

    return process, url, _app


def create_msui_settings_file(content):
    with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
        file_dir.writetext("msui_settings.json", content)


def wait_until_socket_ready(address, initial_delay=0.01, backoff_factor=2, max_delay=1):
    """Wait until the socket at address accepts connections

    This function uses an exponential backoff strategy to try to return fast but also
    allow the other party some time to become ready. The default values correspond to
    infinite retries with the following wait times in-between them in seconds:
    [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1, 1, 1, ...].
    """
    retry_delay = initial_delay
    while True:
        try:
            socket.create_connection(address)
            return
        except ConnectionRefusedError:
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * backoff_factor, max_delay)


class ExceptionMock:
    """
    Replace function calls with raised exceptions
    e.g.
    with mock.patch("requests.get", new=ExceptionMock(requests.exceptions.ConnectionError).raise_exc):
        self._login()
    """
    def __init__(self, exc):
        self.exc = exc

    def raise_exc(self, *args, **kwargs):
        raise self.exc


class LiveSocketTestCase(LiveServerTestCase):

    def _spawn_live_server(self):
        self._process = None
        port_value = self._port_value
        app, sockio, cm, fm = initialize_managers(self.app)
        self._process = multiprocessing.Process(
            target=start_server,
            args=(app, sockio, cm, fm,),
            kwargs={'port': port_value.value})

        self._process.start()

        # We must wait for the server to start listening
        retry_delay = 0.01
        while True:
            if self._can_ping_server():
                break
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 1)
