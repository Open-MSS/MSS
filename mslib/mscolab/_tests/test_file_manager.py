# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_file_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file_manager functionalities

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
from flask_testing import TestCase
import os
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Project, db
from mslib.mscolab.server import APP
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.mscolab import handle_db_seed


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_FileManager(TestCase):
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

    def setUp(self):
        handle_db_seed()
        db.init_app(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.user = get_user(self.userdata[0])
        assert self.user is not None
        assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2])
        self.anotheruser = get_user(self.anotheruserdata[0])
        self._example_data()

    def tearDown(self):
        pass
        # review later when handle_db does not seed for tests
        # db.session.remove()
        # db.drop_all()

    def test_create_project(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="famous")
            assert project.path == flight_path
            assert self.fm.create_project(flight_path, "something to know", self.user) is False
            flight_path, project = self._create_project(flight_path="example_flight_path", content=self.content1)
            assert project.path == flight_path

    def test_get_project_details(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='project2')
            pd = self.fm.get_project_details(project.id, self.user)
            assert pd['description'] == project.description
            assert pd['path'] == project.path
            assert pd['id'] == project.id

    def test_list_projects(self):
        with self.app.test_client():
            self.fm.create_project("first", "info about first", self.user)
            self.fm.create_project("second", "info about second", self.user)
            expected_result = [{'access_level': 'creator',
                                'description': 'info about first',
                                'p_id': 7,
                                'path': 'first'},
                               {'access_level': 'creator',
                                'description': 'info about second',
                                'p_id': 8,
                                'path': 'second'}]
            assert self.fm.list_projects(self.user) == expected_result

    def test_is_admin(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='third')
            assert self.fm.is_admin(self.user.id, project.id)

    @pytest.mark.skip("need an API to set colaborator on fm")
    def test_is_collaborator(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='fourth')
            assert self.anotheruser.id is not None
            self.fm.add_bulk_permission(project.id, self.user, [self.anotheruser.id], "collaborator")
            assert self.fm.is_collaborator(self.anotheruser.id, project.id)

    def test_auth_type(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="aa")
            assert self.fm.auth_type(self.user.id, project.id) != "collaborator"
            assert self.fm.auth_type(self.user.id, project.id) == "creator"

    def test_update_project(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='project3')
            rename_to = "project03"
            self.fm.update_project(project.id, "path", rename_to, self.user)
            ren_project = Project.query.filter_by(path=rename_to).first()
            assert ren_project.id == project.id
            assert ren_project.path == rename_to

    def test_delete_file(self):
        # Todo rename to project
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='project4')
            assert self.fm.delete_file(project.id, self.user)
            assert Project.query.filter_by(path=flight_path).first() is None

    @pytest.mark.skip("needs a review")
    def test_get_authorized_users(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path='project5')
            assert self.fm.get_authorized_users(project.id) == [{'access_level': 'creator',
                                                                 'username': self.userdata[2]}]

    def test_save_file(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project6", content=self.content1)
            # nothing changed
            assert self.fm.save_file(project.id, self.content1, self.user) is False
            assert self.fm.save_file(project.id, self.content2, self.user)

    def test_get_file(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project7")
            assert self.fm.get_file(project.id, self.user).startswith('<?xml version="1.0" encoding="utf-8"?>')

    @pytest.mark.skip("needs a review")
    def test_get_all_changes(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project8")
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            assert len(self.fm.get_all_changes(project.id, self.user)) == 2

    @pytest.mark.skip("needs a review")
    def test_get_change_content(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project8")
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.get_change_content(all_changes[1]["id"]) == self.content1

    @pytest.mark.skip("needs a review")
    def test_set_version_name(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project8")
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.set_version_name(all_changes[1]["id"], project.id, self.user.id, "THIS")

    def test_undo(self):
        pytest.skip('timing problem')
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project8")
            assert self.fm.get_all_changes(project.id, self.user) == []
            assert self.fm.save_file(project.id, self.content1, self.user)
            assert self.fm.save_file(project.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(project.id, self.user)
            assert self.fm.undo(all_changes[1]["id"], self.user)

    def test_fetch_users_without_permission(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project9")
            assert len(self.fm.fetch_users_without_permission(project.id, self.user.id)) > 3

    def test_fetch_users_with_permission(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project9")
            assert self.fm.fetch_users_with_permission(project.id, self.user.id) == []

    def test_import_permission(self):
        with self.app.test_client():
            flight_path8, project8 = self._create_project(flight_path="project8")
            flight_path9, project9 = self._create_project(flight_path="project9")
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

    def _create_project(self, flight_path="firstflight", user=None, content=None):
        if user is None:
            user = self.user
        self.fm.create_project(flight_path, f"info about {flight_path}", user, content=content)
        project = Project.query.filter_by(path=flight_path).first()
        return flight_path, project
