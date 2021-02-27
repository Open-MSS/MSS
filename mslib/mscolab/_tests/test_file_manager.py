# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_file_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file_manager functionalities

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
import requests
import json
import sys
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab import file_manager
from mslib.mscolab.models import User, Project
from mslib.mscolab.server import db, APP
from mslib.mscolab.mscolab import handle_db_seed


@pytest.mark.usefixtures("start_mscolab_server")
@pytest.mark.usefixtures("stop_server")
@pytest.mark.usefixtures("create_data")
class Test_FileManager(object):
    def setup(self):
        if sys.platform ==  'linux':
            assert 'tmp' in mscolab_settings.MSCOLAB_DATA_DIR
        handle_db_seed()
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.url = self.app.config['URL']
        db.init_app(self.app)
        self.fm = file_manager.FileManager(mscolab_settings.MSCOLAB_DATA_DIR)
        self._example_data()
        self.cleanup_pid = set()
        data = {
            'email': 'a',
            'password': 'a'
        }
        r = requests.post(self.url + '/token', data=data)
        self.token = json.loads(r.text)['token']
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def teardown(self):
        with self.app.app_context():
            # Todo refactoring for a new user and remove everything from that user, without collection of p_id
            for p_id in self.cleanup_pid:
                self.fm.delete_file(p_id, self.user)
            db.session.commit()

    def test_create_project(self):
        with self.app.app_context():
            flight_path = "famous"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.create_project(flight_path, "something to know", self.user) is False
            flight_path = "example_flight_path"
            assert self.fm.create_project(flight_path, "something to know", self.user, content=self.content1)
            project = Project.query.filter_by(path=flight_path).first()
            assert project.path == flight_path
            self.cleanup_pid.add(project.id)

    def test_get_project_details(self):
        with self.app.app_context():
            flight_path = 'project2'
            self.fm.create_project(flight_path, "info about project2", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            pd = self.fm.get_project_details(project.id, self.user)
            assert pd['description'] == 'info about project2'
            assert pd['path'] == 'project2'
            assert pd['id'] == 7

    def test_list_projects(self):
        # ToDo check cleanup
        expected_result = [{'access_level': 'creator', 'description': 'a, b', 'p_id': 1, 'path': 'one'},
                           {'access_level': 'collaborator', 'description': 'a, c', 'p_id': 3, 'path': 'three'},
                           {'access_level': 'admin', 'description': 'd', 'p_id': 4, 'path': 'four'}]
        with self.app.app_context():
            assert self.fm.list_projects(self.user) == expected_result

    def test_is_admin(self):
        with self.app.app_context():
            project = Project.query.filter_by(path="four").first()
            assert self.fm.is_admin(self.user.id, project.id)
            project = Project.query.filter_by(path="three").first()
            assert self.fm.is_admin(self.user.id, project.id) is False

    def test_auth_type(self):
        with self.app.app_context():
            project = Project.query.filter_by(path="three").first()
            assert self.fm.auth_type(self.user.id, project.id) == "collaborator"
            project = Project.query.filter_by(path="four").first()
            assert self.fm.auth_type(self.user.id, project.id) == "admin"

    def test_update_project(self):
        with self.app.app_context():
            flight_path = 'project3'
            self.fm.create_project(flight_path, "info about project3", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.fm.update_project(project.id, "path", "project03", self.user)
            ren_project = Project.query.filter_by(path="project03").first()
            self.cleanup_pid.add(ren_project.id)
            assert project.id == ren_project.id

    def test_delete_file(self):
        # Todo rename to project
        with self.app.app_context():
            flight_path = 'project4'
            self.fm.create_project(flight_path, "info about project4", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.delete_file(project.id, self.user)
            assert Project.query.filter_by(path=flight_path).first() is None

    def test_get_authorized_users(self):
        with self.app.app_context():
            flight_path = 'project5'
            self.fm.create_project(flight_path, "info about project5", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_authorized_users(project.id) == [{'access_level': 'creator', 'username': 'a'}]

    def test_save_file(self):
        with self.app.app_context():
            flight_path = "project6"
            assert self.fm.create_project(flight_path, "something to know", self.user, content=self.content1)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            # nothing changed
            assert self.fm.save_file(project.id, self.content1, self.user) is False
            assert self.fm.save_file(project.id, self.content2, self.user)

    def test_get_file(self):
        with self.app.app_context():
            flight_path = "project7"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_file(project.id, self.user).startswith('<?xml version="1.0" encoding="utf-8"?>')

    def test_get_all_changes(self):
        with self.app.app_context():
            flight_path = "project8"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            assert len(self.fm.get_all_changes(project.id, self.user)) == 2

    def test_get_change_content(self):
        with self.app.app_context():
            flight_path = "project8"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.get_change_content(all_changes[1]["id"]) == self.content1

    def test_set_version_name(self):
        with self.app.app_context():
            flight_path = "project8"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.set_version_name(all_changes[1]["id"], project.id, self.user.id, "THIS")

    def test_undo(self):
        with self.app.app_context():
            flight_path = "project8"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.undo(all_changes[1]["id"], self.user)

    def test_fetch_users_without_permission(self):
        with self.app.app_context():
            flight_path = "project9"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert len(self.fm.fetch_users_without_permission(project.id, self.user.id)) > 3

    def test_fetch_users_with_permission(self):
        with self.app.app_context():
            flight_path = "project9"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project.id)
            assert self.fm.fetch_users_with_permission(project.id, self.user.id) == []

    def test_import_permission(self):
        with self.app.app_context():
            flight_path = "project8"
            assert self.fm.create_project(flight_path, "something to know", self.user)

            project8 = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project8.id)
            flight_path = "project9"
            assert self.fm.create_project(flight_path, "something to know", self.user)
            project9 = Project.query.filter_by(path=flight_path).first()
            self.cleanup_pid.add(project9.id)
            assert self.fm.import_permissions(project8.id, project9.id, self.user.id) == (True,
                                                                                          {'add_users': [],
                                                                                           'delete_users': [],
                                                                                           'modify_users': []})

    def _example_data(self):
        self.content1 = """\
<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack>
    <Name>new flight track (1)</Name>
    <ListOfWaypoints>
      <Waypoint flightlevel="0.0" lat="55.15" location="B" lon="-23.74">
        <Comments>Takeoff</Comments>
      </Waypoint>
      <Waypoint flightlevel="350" lat="42.99" location="A" lon="-12.1">
        <Comments></Comments>
      </Waypoint>
      <Waypoint flightlevel="380.0" lat="52.785" location="Shannon" lon="-8.925">
        <Comments>Dive</Comments>
      </Waypoint>
      <Waypoint flightlevel="400.0" lat="48.08" location="EDMO" lon="11.28">
        <Comments></Comments>
      </Waypoint>
      <Waypoint flightlevel="0.0" lat="63.74" location="C" lon="1.73">
        <Comments>Landing</Comments>
      </Waypoint>
    </ListOfWaypoints>
  </FlightTrack>"""
        self.content2 = """\
<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack>
    <Name>new flight track (1)</Name>
    <ListOfWaypoints>
      <Waypoint flightlevel="0.0" lat="55.15" location="B" lon="-23.74">
        <Comments>Takeoff</Comments>
      </Waypoint>
      <Waypoint flightlevel="350" lat="42.99" location="A" lon="-12.1">
        <Comments></Comments>
      </Waypoint>
      </ListOfWaypoints>
  </FlightTrack>"""
