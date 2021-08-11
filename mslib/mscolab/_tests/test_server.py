# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_server
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server functionalities

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
import mslib
from flask import Flask
from flask_testing import TestCase
import os
import pytest
import json
import io

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, User
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.mscolab import handle_db_seed
from mslib.mscolab.server import initialize_managers, check_login, register_user, hello, APP

from werkzeug.urls import url_join
from mslib._tests.utils import (mscolab_register_and_login, mscolab_create_project, mscolab_create_content,
                                mscolab_login, mscolab_delete_user)
from pathlib import Path

DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Init_Server(object):
    def setup(self):
        handle_db_seed()
        self.app = Flask(__name__, static_url_path='')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.user = get_user(self.userdata[0])

    def teardown(self):
        pass

    def test_initialize_managers(self):
        app, sockio, cm, fm = initialize_managers(self.app)
        assert app.config['MSCOLAB_DATA_DIR'] == mscolab_settings.MSCOLAB_DATA_DIR
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_check_login(self):
        with self.app.app_context():
            user = check_login('UV10@uv10', 'uv10')
            assert user.id == self.user.id
            user = check_login('UV10@uv10', 'invalid_password')
            assert user is False
            user = check_login('not_existing', 'beta')
            assert user is False

    def test_register_user(self):
        with self.app.app_context():
            assert register_user('alpha@alpha.org', 'abcdef', 'alpha@alpha.org') == \
                   {'message': 'Oh no, your username cannot contain @ symbol!', 'success': False}
            assert register_user('alpha@alpha.org', 'abcdef', 'alpha') == {"success": True}
            assert register_user('alpha@alpha.org', 'abcdef', 'alpha') == \
                   {'message': 'Oh no, this email ID is already taken!', 'success': False}
            assert register_user('alpha2a@alpha.org', 'abcdef', 'alpha') == \
                   {'message': 'Oh no, this username is already registered', 'success': False}

    def test_hello(self):
        with self.app.app_context():
            assert hello() == "Mscolab server"


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Server(TestCase):
    render_templates = False

    def create_app(self):
        app = APP

        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['LIVESERVER_PORT'] = 0

        return app

    def test_home(self):
        response = self.client.get('/')
        assert response.status_code == 200
        assert b"" in response.data

    def test_hello(self):
        with self.app.test_client() as test_client:
            response = test_client.get('/status')
            assert response.status_code == 200
            assert b"Mscolab server" in response.data

    def test_get_auth_token(self):
        handle_db_seed()
        userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(userdata[0], userdata[1], userdata[2])
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == userdata[1]
            token = data["token"]
            assert User.verify_auth_token(token)
            response = test_client.post('/token', data={"email": userdata[0], "password": "fail"})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "False"

    def test_authorized(self):
        handle_db_seed()
        userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(userdata[0], userdata[1], userdata[2])
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == userdata[1]
            token = data["token"]
            response = test_client.get('/test_authorized', data={"token": token})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "True"
            response = test_client.get('/test_authorized', data={"token": "effsdfs"})
            assert response.data.decode('utf-8') == "False"

    def test_user_register_handler(self):
        handle_db_seed()
        userdata = 'UV10@uv10', 'UV10', 'uv10'
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            response = test_client.post('/register', data={"email": userdata[0],
                                                           "password": userdata[2],
                                                           "username": userdata[1]})
            assert response.status_code == 201
            response = test_client.post('/register', data={"email": userdata[0],
                                                           "pass": "dsss",
                                                           "username": userdata[1]})
            assert response.status_code == 400

    def test_get_user(self):
        handle_db_seed()
        userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(userdata[0], userdata[1], userdata[2])
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == userdata[1]
            token = data["token"]
            response = test_client.get('/user', data={"token": token})
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == userdata[1]

    def test_delete_user(self):
        handle_db_seed()
        userdata = 'UV10@uv10', 'UV10', 'uv10'
        assert add_user(userdata[0], userdata[1], userdata[2])
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == userdata[1]
            token = data["token"]
            response = test_client.post('/delete_user', data={"token": token})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True
            response = test_client.post('/delete_user', data={"token": "dsdsds"})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "False"

    @pytest.mark.skip("to be refactored")
    def test_messages(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(self.url, 'messages')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data["messages"] == []

    @pytest.mark.skip("to be refactored")
    def test_message_attachment(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f3', description='f3 test example')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            projects = json.loads(response.get_data(as_text=True))
            assert projects == {'projects': [{'access_level': 'creator',
                                              'description': 'f3 test example',
                                              'p_id': 7,
                                              'path': 'f3'}]}

            data['p_id'] = projects['projects'][0]['p_id']
            data["message_type"] = 0
            file_name = "fake-text-stream.txt"
            data["file"] = (io.BytesIO(b"some initial text data"), file_name)

            url = url_join(self.url, 'message_attachment')
            response = self.app.test_client().post(url, data=data)
            # Todo Example upload
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True

    @pytest.mark.skip("to be refactored")
    def test_uploads(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f4', description='f4 test example')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            projects = json.loads(response.get_data(as_text=True))
            data['p_id'] = projects['projects'][0]['p_id']
            p_id = data['p_id']
            data["message_type"] = 0
            file_name = "fake-text-stream.txt"
            data["file"] = (io.BytesIO(b"some initial text data"), file_name)
            url = url_join(self.url, 'message_attachment')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            fn = Path(data['path']).name
            url = "%s/uploads/%s/%s" % (self.url, p_id, fn)
            response = self.app.test_client().get(url)
            data = response.get_data(as_text=True)
            assert data == "some initial text data"
            url = "%s/uploads/%s" % (self.url, p_id)
            response = self.app.test_client().get(url)
            result = response.get_data(as_text=True)
            assert "404" in result
            url = "%s/uploads/" % (self.url)
            response = self.app.test_client().get(url)
            result = response.get_data(as_text=True)
            assert "404" in result

    @pytest.mark.skip("to be refactored")
    def test_create_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f1', description='f1 test example')
            assert response.status == '200 OK'
            data = response.get_data(as_text=True)
            assert data == 'True'

    @pytest.mark.skip("to be refactored")
    def test_get_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            content = """\
<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack>
    <Name>F5 test example</Name>
    <ListOfWaypoints>
      <Waypoint flightlevel="0.0" lat="55.15" location="A1" lon="-23.74">
        <Comments>Takeoff</Comments>
      </Waypoint>
      <Waypoint flightlevel="350" lat="42.99" location="A2" lon="-12.1">
        <Comments></Comments>
      </Waypoint>
      </ListOfWaypoints>
  </FlightTrack>"""

            data["path"] = 'f5'
            data['description'] = 'f5 test example'
            data['content'] = content
            url = url_join(self.url, 'create_project')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f5':
                    data['p_id'] = p['p_id']
                    break
            url = url_join(self.url, 'get_project_by_id')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert 'F5 test example' in data['content']

    @pytest.mark.skip("to be refactored")
    def test_get_all_changes(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f14')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f14':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'get_all_changes')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            # ToDo check 2 changes
            assert data['changes'] == []

    @pytest.mark.skip("to be refactored")
    def test_get_change_content(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f15')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'get_change_content')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = response.get_data(as_text=True)
            # ToDo add a test with two revisions
            assert response == 'False'

    @pytest.mark.skip("to be refactored")
    def test_authorized_users(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, self.url, data, path_name='f10')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f10':
                    auth_data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'authorized_users')
            response = self.app.test_client().get(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['users'] == [{'access_level': 'creator', 'username': 'alpha'}]

    @pytest.mark.skip("to be refactored")
    def test_get_projects(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f7')
            assert response.status == '200 OK'
            response = mscolab_create_content(self.app, self.url, data, path_name='f8')
            assert response.status == '200 OK'

            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 2

    @pytest.mark.skip("to be refactored")
    def test_delete_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, self.url, data, path_name='f12')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f12':
                    auth_data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'delete_project')
            response = self.app.test_client().post(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True

    @pytest.mark.skip("to be refactored")
    def test_update_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f16')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f16':
                    data['p_id'] = p['p_id']
                    break
            data['attribute'] = 'path'
            data['value'] = 'example_flight_path'
            url = url_join(self.url, 'update_project')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            content = """\
                    <?xml version="1.0" encoding="utf-8"?>
                      <FlightTrack>
                        <Name>F14 test example</Name>
                        <ListOfWaypoints>
                          <Waypoint flightlevel="100.0" lat="55.15" location="A1" lon="-25.74">
                            <Comments>Takeoff</Comments>
                          </Waypoint>
                          <Waypoint flightlevel="350" lat="42.99" location="A2" lon="-12.1">
                            <Comments></Comments>
                          </Waypoint>
                          </ListOfWaypoints>
                      </FlightTrack>"""
            # not sure if the update API should do this
            # data['attribute'] = "content"
            # data['value'] = content
            # url = url_join(self.url, 'update_project')
            # response = self.app.test_client().post(url, data=data)
            # assert response.status == '200 OK'
            user = User.query.filter_by(emailid='alpha@alpha.org').first()
            self.fm.save_file(int(data['p_id']), content, user, "new")

    @pytest.mark.skip("to be refactored")
    def test_get_project_details(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, self.url, data, path_name='f13')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f13':
                    auth_data['p_id'] = p['p_id']
                    break
            url = url_join(self.url, 'project_details')
            response = self.app.test_client().get(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response == {'description': 'f13', 'id': auth_data['p_id'], 'path': 'f13'}

    @pytest.mark.skip("to be refactored")
    def test_get_users_without_permission(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f15')
            assert response.status == '200 OK'

            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'users_without_permission')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True
            assert len(response['users']) > 1

    @pytest.mark.skip("to be refactored")
    def test_get_users_with_permission(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='f15')
            assert response.status == '200 OK'

            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(self.url, 'users_with_permission')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True
            assert response['users'] == []

    @pytest.mark.skip("to be refactored")
    def test_import_permissions(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='p1')
            assert response.status == '200 OK'
            response = mscolab_create_content(self.app, self.url, data, path_name='p2')
            assert response.status == '200 OK'

            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'p1':
                    data['import_p_id'] = p['p_id']
                if p['path'] == 'p2':
                    data['current_p_id'] = p['p_id']
            url = url_join(self.url, 'import_permissions')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response["success"] is True

    @pytest.mark.skip("to be refactored")
    def test_uniqueness_of_user_id(self):
        """
        creates a user, creates a project, removes the user
        creates a different new user, checks for projects
        should not find anything
        """
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data, path_name='owns_alpha')
            assert response.status == '200 OK'
            mscolab_delete_user(self.app, self.url, 'alpha@alpha.org', 'abcdef')
            response = mscolab_register_and_login(self.app, self.url, 'delta@delta.org', 'abcdef', 'delta')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 0

    @pytest.mark.skip("to be refactored")
    def test_token_dependency_to_project(self):
        """
        creates a user, creates a project, checks that there is only 1 project
        fetches a valid token from an other user
        replaces the token by keeping the user information
        finds only projects related to the changed token
        """
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'user@alpha.org', 'user', 'user')
            assert response.status == '200 OK'
            data_1 = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, self.url, data_1, path_name='data_1')
            assert response.status == '200 OK'
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data_1)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 1
            response = mscolab_login(self.app, self.url, 'a', 'a')
            data_a = json.loads(response.get_data(as_text=True))
            data_1['token'] = data_a['token']
            url = url_join(self.url, 'projects')
            response = self.app.test_client().get(url, data=data_1)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 3
