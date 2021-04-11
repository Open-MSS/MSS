# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_server
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server functionalities

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
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
import io
from pathlib import Path
from flask import json
from werkzeug.urls import url_join
from mslib.mscolab.server import APP
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab import server
from mslib.mscolab.models import User
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib._tests.utils import (mscolab_register_user,
                                mscolab_register_and_login, mscolab_create_content,
                                mscolab_create_project, mscolab_delete_all_projects,
                                mscolab_delete_user, mscolab_login)


class Test_Init_Server(object):
    def setup(self):
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR

    def test_initialize_managers(self):
        app, sockio, cm, fm = server.initialize_managers(self.app)
        assert app.config['MSCOLAB_DATA_DIR'] == mscolab_settings.MSCOLAB_DATA_DIR
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__


class Test_Server(object):
    def setup(self):
        mscolab_settings.enable_basic_http_authentication = False
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        _app, self.sockio, self.cm, self.fm = server.initialize_managers(self.app)

    def teardown(self):
        with self.app.app_context():
            mscolab_delete_all_projects(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            mscolab_delete_all_projects(self.app, MSCOLAB_URL_TEST, 'user@alpha.org', 'user', 'user')
            for em, pw in [('alpha@alpha.org', 'abcdef'),
                           ('user2@example.com', 'user2'),
                           ('delta@delta.org', 'abcdef'),
                           ('otheruser@other.org', 'other'),
                           ('user@alpha.org', 'user')
                           ]:
                server.register_user(em, pw, 'test')
                mscolab_delete_user(self.app, MSCOLAB_URL_TEST, em, pw)
            server.db.session.commit()

    def test_check_login(self):
        with self.app.app_context():
            user = server.check_login('a', 'a')
            assert user.id == 8
            user = server.check_login('a', 'invalid_password')
            assert user is False
            user = server.check_login('not_existing', 'beta')
            assert user is False

    def test_register_user(self):
        with self.app.app_context():
            assert server.register_user('alpha@alpha.org', 'abcdef', 'alpha@alpha.org') == \
                   {'message': 'Oh no, your username cannot contain @ symbol!', 'success': False}
            assert server.register_user('alpha@alpha.org', 'abcdef', 'alpha') == {"success": True}
            assert server.register_user('alpha@alpha.org', 'abcdef', 'alpha') == \
                   {'message': 'Oh no, this email ID is already taken!', 'success': False}
            assert server.register_user('alpha2a@alpha.org', 'abcdef', 'alpha') == \
                   {'message': 'Oh no, this username is already registered', 'success': False}

    def test_verify_user(self):
        pass

    def test_home(self):
        pytest.skip("Application is not able to create a URL adapter without SERVER_NAME")
        with self.app.app_context():
            result = server.home()
            assert "!DOCTYPE html" in result

    def test_status(self):
        with self.app.app_context():
            assert server.hello() == "Mscolab server"

    def test_get_auth_token(self):
        data = {
            'email': 'a',
            'password': 'a'
        }
        url = url_join(MSCOLAB_URL_TEST, 'token')
        response = self.app.test_client().post(url, data=data)
        assert response.status == '200 OK'
        data = json.loads(response.get_data(as_text=True))
        assert 'token' in data
        assert 'user' in data

        data = {
            'email': 'a',
            'password': 'wrong password'
        }
        response = self.app.test_client().post(url, data=data)
        assert response.status == '200 OK'
        assert response.get_data(as_text=True) == "False"

    def test_authorized(self):
        # ToDo Token needs to be checked for the user
        data = {
            'email': 'a',
            'password': 'a'
        }
        url = url_join(MSCOLAB_URL_TEST, 'token')
        response = self.app.test_client().post(url, data=data)
        assert response.status == '200 OK'
        data = json.loads(response.get_data(as_text=True))
        url = url_join(MSCOLAB_URL_TEST, 'test_authorized')
        response = self.app.test_client().get(url, data=data)
        assert response.status == '200 OK'
        assert response.get_data(as_text=True) == "True"

        # wrong token
        data['token'] = "wrong"
        url = url_join(MSCOLAB_URL_TEST, 'test_authorized')
        response = self.app.test_client().get(url, data=data)
        assert response.status == '200 OK'
        assert response.get_data(as_text=True) == "False"

    def test_user_register_handler(self):
        response = mscolab_register_user(self.app, MSCOLAB_URL_TEST, 'user2', 'user2', 'u2')
        assert response.status == '200 OK'
        data = json.loads(response.get_data(as_text=True))
        assert data['message'] == 'Oh no, your email ID is not valid!'
        assert data['success'] is False

        response = mscolab_register_user(self.app, MSCOLAB_URL_TEST, 'user2@example.com', 'user2', 'u2')
        assert response.status == '201 CREATED'
        data = json.loads(response.get_data(as_text=True))
        assert data['success'] is True

    def test_get_user(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST,
                                                  'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(MSCOLAB_URL_TEST, 'user')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['user']['username'] == 'alpha'

    def test_delete_user(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(MSCOLAB_URL_TEST, 'delete_user')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data["success"] is True

    def test_messages(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(MSCOLAB_URL_TEST, 'messages')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data["messages"] == []

    def test_message_attachment(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, MSCOLAB_URL_TEST, response,
                                                    path='f3', description='f3 test example')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
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

            url = url_join(MSCOLAB_URL_TEST, 'message_attachment')
            response = self.app.test_client().post(url, data=data)
            # Todo Example upload
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True

    def test_uploads(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, MSCOLAB_URL_TEST, response,
                                                    path='f4', description='f4 test example')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            projects = json.loads(response.get_data(as_text=True))
            data['p_id'] = projects['projects'][0]['p_id']
            p_id = data['p_id']
            data["message_type"] = 0
            file_name = "fake-text-stream.txt"
            data["file"] = (io.BytesIO(b"some initial text data"), file_name)
            url = url_join(MSCOLAB_URL_TEST, 'message_attachment')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            fn = Path(data['path']).name
            url = "%s/uploads/%s/%s" % (MSCOLAB_URL_TEST, p_id, fn)
            response = self.app.test_client().get(url)
            data = response.get_data(as_text=True)
            assert data == "some initial text data"
            url = "%s/uploads/%s" % (MSCOLAB_URL_TEST, p_id)
            response = self.app.test_client().get(url)
            result = response.get_data(as_text=True)
            assert "404" in result
            url = "%s/uploads/" % (MSCOLAB_URL_TEST)
            response = self.app.test_client().get(url)
            result = response.get_data(as_text=True)
            assert "404" in result

    def test_error413(self):
        pass

    def test_create_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, MSCOLAB_URL_TEST, response,
                                                    path='f1', description='f1 test example')
            assert response.status == '200 OK'
            data = response.get_data(as_text=True)
            assert data == 'True'

    def test_get_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
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
            url = url_join(MSCOLAB_URL_TEST, 'create_project')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f5':
                    data['p_id'] = p['p_id']
                    break
            url = url_join(MSCOLAB_URL_TEST, 'get_project')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert 'F5 test example' in data['content']

    def test_get_all_changes(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f14')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f14':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'get_all_changes')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            # ToDo check 2 changes
            assert data['changes'] == []

    def test_get_change_content(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f15')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'get_change_content')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = response.get_data(as_text=True)
            # ToDo add a test with two revisions
            assert response == 'False'

    def test_set_version_name(self):
        pass

    def test_authorized_users(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f10')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f10':
                    auth_data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'authorized_users')
            response = self.app.test_client().get(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['users'] == [{'access_level': 'creator', 'username': 'alpha'}]

    def test_get_projects(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f7')
            assert response.status == '200 OK'
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f8')
            assert response.status == '200 OK'

            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 2

    def test_delete_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f12')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f12':
                    auth_data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'delete_project')
            response = self.app.test_client().post(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True

    def test_update_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f16')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f16':
                    data['p_id'] = p['p_id']
                    break
            data['attribute'] = 'path'
            data['value'] = 'example_flight_path'
            url = url_join(MSCOLAB_URL_TEST, 'update_project')
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
            # url = url_join(MSCOLAB_URL_TEST, 'update_project')
            # response = self.app.test_client().post(url, data=data)
            # assert response.status == '200 OK'
            user = User.query.filter_by(emailid='alpha@alpha.org').first()
            self.fm.save_file(int(data['p_id']), content, user, "new")

    def test_get_project_details(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            auth_data = data
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f13')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f13':
                    auth_data['p_id'] = p['p_id']
                    break
            url = url_join(MSCOLAB_URL_TEST, 'project_details')
            response = self.app.test_client().get(url, data=auth_data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response == {'description': 'f13', 'id': auth_data['p_id'], 'path': 'f13'}

    def test_undo_ftml(self):
        pass

    def test_get_users_without_permission(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f15')
            assert response.status == '200 OK'

            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'users_without_permission')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True
            assert len(response['users']) > 1

    def test_get_users_with_permission(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='f15')
            assert response.status == '200 OK'

            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'f15':
                    data['p_id'] = p['p_id']
                    break

            url = url_join(MSCOLAB_URL_TEST, 'users_with_permission')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response['success'] is True
            assert response['users'] == []

    def test_import_permissions(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='p1')
            assert response.status == '200 OK'
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='p2')
            assert response.status == '200 OK'

            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            for p in response['projects']:
                if p['path'] == 'p1':
                    data['import_p_id'] = p['p_id']
                if p['path'] == 'p2':
                    data['current_p_id'] = p['p_id']
            url = url_join(MSCOLAB_URL_TEST, 'import_permissions')
            response = self.app.test_client().post(url, data=data)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert response["success"] is True

    def test_uniqueness_of_user_id(self):
        """
        creates a user, creates a project, removes the user
        creates a different new user, checks for projects
        should not find anything
        """
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef', 'alpha')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data, path_name='owns_alpha')
            assert response.status == '200 OK'
            mscolab_delete_user(self.app, MSCOLAB_URL_TEST, 'alpha@alpha.org', 'abcdef')
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'delta@delta.org', 'abcdef', 'delta')
            assert response.status == '200 OK'
            data = json.loads(response.get_data(as_text=True))
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 0

    def test_token_dependency_to_project(self):
        """
        creates a user, creates a project, checks that there is only 1 project
        fetches a valid token from an other user
        replaces the token by keeping the user information
        finds only projects related to the changed token
        """
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, MSCOLAB_URL_TEST, 'user@alpha.org', 'user', 'user')
            assert response.status == '200 OK'
            data_1 = json.loads(response.get_data(as_text=True))
            response = mscolab_create_content(self.app, MSCOLAB_URL_TEST, data_1, path_name='data_1')
            assert response.status == '200 OK'
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data_1)
            assert response.status == '200 OK'
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 1
            response = mscolab_login(self.app, MSCOLAB_URL_TEST, 'a', 'a')
            data_a = json.loads(response.get_data(as_text=True))
            data_1['token'] = data_a['token']
            url = url_join(MSCOLAB_URL_TEST, 'projects')
            response = self.app.test_client().get(url, data=data_1)
            response = json.loads(response.get_data(as_text=True))
            assert len(response['projects']) == 3
