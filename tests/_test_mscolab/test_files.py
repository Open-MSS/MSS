# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_files
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file based handlers

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import os
import pytest

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import User, Operation, Permission, Change, Message
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.utils import get_recent_op_id
from tests.utils import XML_CONTENT1, XML_CONTENT2, XML_CONTENT3


class Test_Files:
    @pytest.fixture(autouse=True)
    def setup(self, mscolab_app, mscolab_managers):
        self.app = mscolab_app
        _, _, self.fm = mscolab_managers

        self.userdata = 'UV11@uv11', 'UV11', 'uv11'
        self.userdata2 = 'UV12@uv12', 'UV12', 'uv12'

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_user(self.userdata2[0], self.userdata2[1], self.userdata2[2])

        self.user = get_user(self.userdata[0])
        self.user2 = get_user(self.userdata2[0])
        assert self.user is not None
        self.file_message_counter = [0] * 2
        self._example_data()
        with self.app.app_context():
            yield

    def test_create_operation(self):
        with self.app.test_client():
            # test for blank character in path
            assert self.fm.create_operation('test path', 'test desc.', self.user) is False
            # test for normal path
            assert self.fm.create_operation('test_path', 'test desc.', self.user) is True
            # test for '/' in path
            assert self.fm.create_operation('test/path', 'sth', self.user) is False
            # check file existence
            assert os.path.exists(os.path.join(mscolab_settings.FILE_DATA, 'test_path')) is True
            # check creation in db
            p = Operation.query.filter_by(path="test_path").first()
            assert p is not None
            # check permission for author
            perms = Permission.query.filter_by(op_id=p.id, access_level="creator").all()
            assert len(perms) == 1
            assert perms[0].u_id == self.user.id

    def test_operations(self):
        with self.app.test_client():
            operations = self.fm.list_operations(self.user)
            assert len(operations) == 0
            assert self.fm.create_operation('test_path', 'test desc.', self.user) is True
            operations = self.fm.list_operations(self.user)
            assert len(operations) == 1

    def test_is_creator(self):
        with self.app.test_client():
            assert self.fm.create_operation('test_path', 'test desc.', self.user) is True
            op_id = get_recent_op_id(self.fm, self.user)
            u_id = self.user.id
            assert self.fm.is_creator(u_id, op_id) is True
            undefined_op_id = 123
            assert self.fm.is_creator(u_id, undefined_op_id) is False
            no_perm_op_id = 2
            assert self.fm.is_creator(u_id, no_perm_op_id) is False

    def test_file_save(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation77")
            assert self.fm.save_file(operation.id, XML_CONTENT1, self.user)
            assert self.fm.get_file(operation.id, self.user) == XML_CONTENT1
            assert self.fm.save_file(operation.id, XML_CONTENT2, self.user)
            assert self.fm.get_file(operation.id, self.user) == XML_CONTENT2
            # check if change is saved properly
            changes = self.fm.get_all_changes(operation.id, self.user)
            assert len(changes) == 2

    def test_cant_save(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation911")
            assert self.fm.save_file(operation.id, "text", self.user) is False
            incomplete = """<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack version="9.1.0">
    <ListOfWaypoints/>
  </FlightTrack>"""
            assert self.fm.save_file(operation.id, incomplete, self.user) is False
            incomplete = """<?xml version="1.0" encoding="utf-8"?>
  <FlightTrack version="9.1.0.">
    <ListOfWaypoints>
      <Waypoint flightlevel="350">
        <Comments></Comments>
      </Waypoint>
      <Waypoint flightlevel="350">
        <Comments></Comments>
      </Waypoint>
    </ListOfWaypoints>
  </FlightTrack>"""
            assert self.fm.save_file(operation.id, incomplete, self.user) is False

    def test_stub_data(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operationstub")
            content = self.fm.get_file(operation.id, self.user)
            assert flight_path == "operationstub"
            assert content == mscolab_settings.STUB_CODE

    def test_undo(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation7", content=XML_CONTENT1)
            assert self.fm.save_file(operation.id, XML_CONTENT2, self.user)
            assert self.fm.save_file(operation.id, XML_CONTENT3, self.user)
            changes = Change.query.filter_by(op_id=operation.id).all()
            assert changes is not None
            assert changes[0].id == 1
            assert self.fm.undo_changes(changes[0].id, self.user) is True
            assert len(self.fm.get_all_changes(operation.id, self.user)) == 3
            assert XML_CONTENT2 == self.fm.get_file(operation.id, self.user)

    def test_get_operation(self):
        with self.app.test_client():
            self._create_operation(flight_path="operation9")
            op_id = get_recent_op_id(self.fm, self.user)
            assert self.fm.get_file(op_id, self.user) is not False
            user2 = User.query.filter_by(emailid=self.userdata2[0]).first()
            assert self.fm.get_file(op_id, user2) is False

    def test_authorized_users(self):
        with self.app.test_client():
            self._create_operation(flight_path="operation10", content=self.content1)
            op_id = get_recent_op_id(self.fm, self.user)
            assert len(self.fm.get_authorized_users(op_id)) == 1

    def test_modify_operation(self):
        with self.app.test_client():
            self._create_operation(flight_path="path")
            op_id = get_recent_op_id(self.fm, self.user)
            # testing for wrong characters in path like ' ', '/'
            assert self.fm.update_operation(op_id, 'path', 'dummy wrong', self.user) is False
            assert self.fm.update_operation(op_id, 'path', 'dummy/wrong', self.user) is False
            assert self.fm.update_operation(op_id, 'path', 'dummy', self.user) is True
            assert os.path.exists(os.path.join(mscolab_settings.FILE_DATA, 'dummy'))
            assert self.fm.update_operation(op_id, 'description', 'dummy', self.user) is True

    def test_delete_operation(self):
        with self.app.test_client():
            self._create_operation(flight_path="f3")
            op_id = get_recent_op_id(self.fm, self.user)
            assert self.fm.delete_operation(op_id, self.user2) is False
            assert self.fm.delete_operation(op_id, self.user) is True
            assert self.fm.delete_operation(op_id, self.user) is False
            permissions = Permission.query.filter_by(op_id=op_id).all()
            assert len(permissions) == 0
            operations_db = Operation.query.filter_by(id=op_id).all()
            assert len(operations_db) == 0
            changes = Change.query.filter_by(op_id=op_id).all()
            assert len(changes) == 0
            messages = Message.query.filter_by(op_id=op_id).all()
            assert len(messages) == 0

    def _example_data(self):
        self.content1 = """<?xml version="1.0" encoding="utf-8"?>
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
        self.content2 = """<?xml version="1.0" encoding="utf-8"?>
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

    def _create_operation(self, flight_path="firstflight", user=None, content=None):
        if user is None:
            user = self.user
        self.fm.create_operation(flight_path, f"info about {flight_path}", user, content=content)
        operation = Operation.query.filter_by(path=flight_path).first()
        return flight_path, operation
