# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides utils for pytest to test mslib modules

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Joern Ungermann
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
import fs
import requests
from werkzeug.urls import url_join
from mslib.mscolab.server import register_user
from flask import json
from mslib._tests.constants import MSS_CONFIG_PATH


def callback_ok_image(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'image/png')


def callback_ok_xml(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'text/xml')


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
    url = url_join(msc_url, 'register')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_register_and_login(app, msc_url, email, password, username):
    register_user(email, password, username)
    data = {
        'email': email,
        'password': password
    }
    url = url_join(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_login(app, msc_url, email='a', password='a'):
    data = {
        'email': email,
        'password': password
    }
    url = url_join(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_user(app, msc_url, email, password):
    with app.app_context():
        response = mscolab_login(app, msc_url, email, password)
        if response.status == '200 OK':
            data = json.loads(response.get_data(as_text=True))
            url = url_join(msc_url, 'delete_user')
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
    url = url_join(msc_url, 'create_project')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_all_projects(app, msc_url, email, password, username):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = url_join(msc_url, 'projects')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['projects']:
        data['p_id'] = p['p_id']
        url = url_join(msc_url, 'delete_project')
        response = app.test_client().post(url, data=data)


def mscolab_create_project(app, msc_url, response, path='f', description='description'):
    data = json.loads(response.get_data(as_text=True))
    data["path"] = path
    data['description'] = description
    url = url_join(msc_url, 'create_project')
    response = app.test_client().post(url, data=data)
    return data, response


def mscolab_get_project_id(app, msc_url, email, password, username, path):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = url_join(msc_url, 'projects')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['projects']:
        if p['path'] == path:
            return p['p_id']


def create_mss_settings_file(content):
    with fs.open_fs(MSS_CONFIG_PATH) as file_dir:
        file_dir.writetext("mss_settings.json", content)
