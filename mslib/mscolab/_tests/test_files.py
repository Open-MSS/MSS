# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_files
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file based handlers

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
# ToDo have to be merged into test_file_manager
from flask_testing import TestCase
import os
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import User, Project, Permission, Change, Message, db
from mslib.mscolab.server import APP
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.utils import get_recent_pid


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Files(TestCase):
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
        handle_db_reset()
        db.init_app(self.app)

        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        self.userdata = 'UV11@uv11', 'UV11', 'uv11'
        self.userdata2 = 'UV12@uv12', 'UV12', 'uv12'

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_user(self.userdata2[0], self.userdata2[1], self.userdata2[2])

        self.user = get_user(self.userdata[0])
        self.user2 = get_user(self.userdata2[0])
        assert self.user is not None
        self.file_message_counter = [0] * 2
        self._example_data()

    def tearDown(self):
        pass

    def test_create_project(self):
        with self.app.test_client():
            # test for blank character in path
            assert self.fm.create_project('test path', 'test desc.', self.user) is False
            # test for normal path
            assert self.fm.create_project('test_path', 'test desc.', self.user) is True
            # test for '/' in path
            assert self.fm.create_project('test/path', 'sth', self.user) is False
            # check file existence
            assert os.path.exists(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_path')) is True
            # check creation in db
            p = Project.query.filter_by(path="test_path").first()
            assert p is not None
            # check permission for author
            perms = Permission.query.filter_by(p_id=p.id, access_level="creator").all()
            assert len(perms) == 1
            assert perms[0].u_id == self.user.id

    def test_projects(self):
        with self.app.test_client():
            projects = self.fm.list_projects(self.user)
            assert len(projects) == 0
            assert self.fm.create_project('test_path', 'test desc.', self.user) is True
            projects = self.fm.list_projects(self.user)
            assert len(projects) == 1

    def test_is_admin(self):
        with self.app.test_client():
            assert self.fm.create_project('test_path', 'test desc.', self.user) is True
            p_id = get_recent_pid(self.fm, self.user)
            u_id = self.user.id
            assert self.fm.is_admin(u_id, p_id) is True
            undefined_p_id = 123
            assert self.fm.is_admin(u_id, undefined_p_id) is False
            no_perm_p_id = 2
            assert self.fm.is_admin(u_id, no_perm_p_id) is False

    def test_file_save(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project77")
            assert self.fm.save_file(project.id, "beta", self.user)
            assert self.fm.get_file(project.id, self.user) == "beta"
            assert self.fm.save_file(project.id, "gamma", self.user)
            assert self.fm.get_file(project.id, self.user) == "gamma"
            # check if change is saved properly
            changes = self.fm.get_all_changes(project.id, self.user)
            assert len(changes) == 2

    def test_undo(self):
        with self.app.test_client():
            flight_path, project = self._create_project(flight_path="project7", content="alpha")
            assert self.fm.save_file(project.id, "beta", self.user)
            assert self.fm.save_file(project.id, "gamma", self.user)
            changes = Change.query.filter_by(p_id=project.id).all()
            assert changes is not None
            assert changes[0].id == 1
            assert self.fm.undo(changes[0].id, self.user) is True
            assert len(self.fm.get_all_changes(project.id, self.user)) == 3
            assert "beta" in self.fm.get_file(project.id, self.user)

    def test_get_project(self):
        with self.app.test_client():
            self._create_project(flight_path="project9")
            p_id = get_recent_pid(self.fm, self.user)
            assert self.fm.get_file(p_id, self.user) is not False
            user2 = User.query.filter_by(emailid=self.userdata2[0]).first()
            assert self.fm.get_file(p_id, user2) is False

    def test_authorized_users(self):
        with self.app.test_client():
            self._create_project(flight_path="project10", content=self.content1)
            p_id = get_recent_pid(self.fm, self.user)
            assert len(self.fm.get_authorized_users(p_id)) == 1

    def test_modify_project(self):
        with self.app.test_client():
            self._create_project(flight_path="path")
            p_id = get_recent_pid(self.fm, self.user)
            # testing for wrong characters in path like ' ', '/'
            assert self.fm.update_project(p_id, 'path', 'dummy wrong', self.user) is False
            assert self.fm.update_project(p_id, 'path', 'dummy/wrong', self.user) is False
            assert self.fm.update_project(p_id, 'path', 'dummy', self.user) is True
            assert os.path.exists(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'dummy'))
            assert self.fm.update_project(p_id, 'description', 'dummy', self.user) is True

    def test_delete_project(self):
        with self.app.test_client():
            self._create_project(flight_path="f3")
            p_id = get_recent_pid(self.fm, self.user)
            assert self.fm.delete_file(p_id, self.user2) is False
            assert self.fm.delete_file(p_id, self.user) is True
            assert self.fm.delete_file(p_id, self.user) is False
            permissions = Permission.query.filter_by(p_id=p_id).all()
            assert len(permissions) == 0
            projects_db = Project.query.filter_by(id=p_id).all()
            assert len(projects_db) == 0
            changes = Change.query.filter_by(p_id=p_id).all()
            assert len(changes) == 0
            messages = Message.query.filter_by(p_id=p_id).all()
            assert len(messages) == 0

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
