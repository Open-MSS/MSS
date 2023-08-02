# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_file_manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file_manager functionalities

    This file is part of MSS.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2023 by the MSS team, see AUTHORS.
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
from mslib.mscolab.models import Operation
from mslib.mscolab.server import APP
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.mscolab import handle_db_reset


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
        handle_db_reset()
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        self.fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])

        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        self.user = get_user(self.userdata[0])
        assert self.user is not None
        assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2])
        self.anotheruser = get_user(self.anotheruserdata[0])
        assert add_user('UV30@uv30', 'UV30', 'uv30')
        self.vieweruser = get_user('UV30@uv30')
        assert add_user('UV40@uv40', 'UV40', 'uv40')
        self.collaboratoruser = get_user('UV40@uv40')
        assert add_user('UV50@uv50', 'UV50', 'uv50')
        self.op2user = get_user('UV50@uv50')
        assert add_user('UV60@uv60', 'UV60', 'uv60')
        self.op2vieweruser = get_user('UV60@uv60')
        assert add_user('UV70@uv70', 'UV70', 'uv70')
        self.user1 = get_user('UV70@uv70')
        assert add_user('UV80@uv80', 'UV80', 'uv80')
        self.adminuser = get_user('UV80@uv80')
        self._example_data()

    def tearDown(self):
        pass

    def test_fetch_operation_creator(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="more_than_one")
            assert operation.path == flight_path
            assert self.fm.fetch_operation_creator(operation.id, self.user.id) == self.user.username

    def test_create_operation(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="famous")
            assert operation.path == flight_path
            assert self.fm.create_operation(flight_path, "something to know", self.user) is False
            flight_path, operation = self._create_operation(flight_path="example_flight_path", content=self.content1)
            assert operation.path == flight_path

    def test_get_operation_details(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='operation2')
            pd = self.fm.get_operation_details(operation.id, self.user)
            assert pd['description'] == operation.description
            assert pd['path'] == operation.path
            assert pd['id'] == operation.id

    def test_list_operations(self):
        with self.app.test_client():
            self.fm.create_operation("first", "info about first", self.user)
            self.fm.create_operation("second", "info about second", self.user)
            expected_result = [{'access_level': 'creator',
                                "active": True,
                                'category': 'default',
                                'description': 'info about first',
                                'op_id': 1,
                                'path': 'first'},
                               {'access_level': 'creator',
                                "active": True,
                                'category': 'default',
                                'description': 'info about second',
                                'op_id': 2,
                                'path': 'second'}]
            assert self.fm.list_operations(self.user) == expected_result

    def test_is_creator(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='third')
            assert self.fm.is_creator(self.user.id, operation.id)

    def test_is_collaborator(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='fourth')
            assert self.anotheruser.id is not None
            self.fm.add_bulk_permission(operation.id, self.user, [self.anotheruser.id], "collaborator")
            assert self.fm.is_collaborator(self.anotheruser.id, operation.id)

    def test_is_non_admin_member(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='fifth')
            assert self.anotheruser.id is not None
            self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "viewer")
            assert self.vieweruser.id is not None
            assert self.fm.is_admin(self.vieweruser.id, operation.id) is False

    def test_is_viewer(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="test_flight")
            assert operation.path == flight_path
            self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "viewer")
            assert self.fm.is_admin(self.vieweruser.id, operation.id) is False
            assert self.fm.is_creator(self.vieweruser.id, operation.id) is False
            assert self.fm.is_collaborator(self.vieweruser.id, operation.id) is False
            assert self.fm.is_viewer(self.vieweruser.id, operation.id) is True
            assert self.fm.is_member(self.vieweruser.id, operation.id) is True

            # cross check with creator self.user
            assert self.fm.is_creator(self.user.id, operation.id) is True
            assert self.fm.is_collaborator(self.user.id, operation.id) is False
            assert self.fm.is_viewer(self.user.id, operation.id) is False

    def test_is_member(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="sunset")
            assert operation.path == flight_path
            assert self.fm.is_member(82322, operation.id) is False
            assert self.fm.is_member(self.user.id, operation.id) is True

    def test_auth_type(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="aa")
            assert self.fm.auth_type(self.user.id, operation.id) != "collaborator"
            assert self.fm.auth_type(self.user.id, operation.id) == "creator"

    def test_update_operation(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='operation3')
            rename_to = "operation03"
            self.fm.update_operation(operation.id, "path", rename_to, self.user)
            ren_operation = Operation.query.filter_by(path=rename_to).first()
            assert ren_operation.id == operation.id
            assert ren_operation.path == rename_to

    def test_delete_file(self):
        # Todo rename "file" to operation
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='operation4')
            assert self.fm.delete_file(operation.id, self.user)
            assert Operation.query.filter_by(path=flight_path).first() is None

    def test_get_authorized_users(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path='operation5')
            assert self.fm.get_authorized_users(operation.id) == [{'access_level': 'creator',
                                                                   'username': self.userdata[1]}]

    def test_save_file(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation6", content=self.content1)
            # nothing changed
            assert self.fm.save_file(operation.id, self.content1, self.user) is False
            assert self.fm.save_file(operation.id, self.content2, self.user)

    def test_get_file(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation7")
            assert self.fm.get_file(operation.id, self.user).startswith('<?xml version="1.0" encoding="utf-8"?>')

    def test_get_all_changes(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation8")
            assert self.fm.get_all_changes(operation.id, self.user) == []
            assert self.fm.save_file(operation.id, self.content1, self.user)
            assert self.fm.save_file(operation.id, self.content2, self.user)
            changes = self.fm.get_all_changes(operation.id, self.user)
            assert len(changes) == 2

    def test_get_change_content(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation8")
            assert self.fm.get_all_changes(operation.id, self.user) == []
            assert self.fm.save_file(operation.id, self.content1, self.user)
            assert self.fm.save_file(operation.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            assert self.fm.get_change_content(all_changes[1]["id"]) == self.content1

    def test_set_version_name(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation8")
            assert self.fm.get_all_changes(operation.id, self.user) == []
            assert self.fm.save_file(operation.id, self.content1, self.user)
            assert self.fm.save_file(operation.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            # creator
            assert self.fm.set_version_name(all_changes[1]["id"], operation.id, self.user.id, "THIS")
            # check collaborator
            self.fm.add_bulk_permission(operation.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation.id)
            assert self.fm.set_version_name(all_changes[1]["id"], operation.id, self.collaboratoruser.id, "THIS")
            # check viewer
            self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "viewer")
            assert self.fm.is_viewer(self.vieweruser.id, operation.id)
            assert self.fm.set_version_name(all_changes[1]["id"], operation.id, self.vieweruser.id, "THIS") is False

    def test_undo(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation8")
            assert self.fm.get_all_changes(operation.id, self.user) == []
            assert self.fm.save_file(operation.id, self.content1, self.user)
            assert self.fm.save_file(operation.id, self.content2, self.user)
            all_changes = self.fm.get_all_changes(operation.id, self.user)
            # crestor
            assert self.fm.undo(all_changes[1]["id"], self.user)
            # check collaborator
            self.fm.add_bulk_permission(operation.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation.id)
            assert self.fm.undo(all_changes[1]["id"], self.collaboratoruser)
            # check viewer
            self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "viewer")
            assert self.fm.is_viewer(self.vieweruser.id, operation.id)
            assert self.fm.undo(all_changes[1]["id"], self.vieweruser) is False

    def test_fetch_users_without_permission(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation9")
            assert len(self.fm.fetch_users_without_permission(operation.id, self.user.id)) == 7

    def test_fetch_users_with_permission(self):
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="operation9")
            assert self.fm.fetch_users_with_permission(operation.id, self.user.id) == []

    def test_delete_bulk_permission_for_creators(self):
        with self.app.test_client():
            flight_path, operation1 = self._create_operation(flight_path="testflight", user=self.user)
            assert self.fm.is_creator(self.user.id, operation1.id)
            assert self.user.id is not None
            self.fm.add_bulk_permission(operation1.id, self.user, [self.anotheruser.id], "collaborator")
            assert self.fm.is_collaborator(self.anotheruser.id, operation1.id)
            self.fm.add_bulk_permission(operation1.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation1.id)
            flight_path1, operation2 = self._create_operation(flight_path="testflight1", user=self.op2user)
            assert self.fm.is_creator(self.op2user.id, operation2.id)
            assert self.op2user.id is not None
            # user (creator of operation1) has no right leave operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.user, [self.user.id]) is False
            # user (creator of operation1) has the right to remove anotheruser from the operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.user, [self.anotheruser.id]) is True
            # op2user (creator of operation2) has no right to remove collaboratoruser of operation1 from operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.op2user, [self.collaboratoruser.id]) is False
            # op2user (creator of operation2) has no right to remove anotheruser of operation1 from operation2
            assert self.fm.delete_bulk_permission(operation2.id, self.op2user, [self.anotheruser.id]) is False

    def test_delete_bulk_permission_for_members(self):
        with self.app.test_client():
            flight_path, operation1 = self._create_operation(flight_path="testflight", user=self.user)
            assert self.fm.is_creator(self.user.id, operation1.id)
            assert self.user.id is not None
            self.fm.add_bulk_permission(operation1.id, self.user, [self.anotheruser.id], "collaborator")
            assert self.fm.is_collaborator(self.anotheruser.id, operation1.id)
            self.fm.add_bulk_permission(operation1.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation1.id)
            self.fm.add_bulk_permission(operation1.id, self.user, [self.vieweruser.id], "viewer")
            assert self.fm.is_viewer(self.vieweruser.id, operation1.id)
            flight_path1, operation2 = self._create_operation(flight_path="testflight1", user=self.op2user)
            assert self.fm.is_creator(self.op2user.id, operation2.id)
            assert self.op2user.id is not None
            self.fm.add_bulk_permission(operation2.id, self.op2user, [self.op2vieweruser.id], "collaborator")
            # collaboratoruser of operation1 has no right to remove vieweruser from the operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.collaboratoruser, [self.vieweruser.id]) is False
            # The below assertion fails in stable 6.1
            # The change is so that vieweruser (any user other than creator) can leave the operation
            # vieweruser of operation1 has the right to leave operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.vieweruser, [self.vieweruser.id]) is True
            # collaboratoruser of operation1 has no right to remove op2vieweruser of operation2 from operation2
            assert self.fm.delete_bulk_permission(
                operation2.id, self.collaboratoruser, [self.op2vieweruser.id]
            ) is False
            # op2vieweruser of operation2 has no right to remove collaboratoruser of operation1 from operation2
            assert self.fm.delete_bulk_permission(
                operation2.id, self.op2vieweruser, [self.collaboratoruser.id]
            ) is False

    def test_delete_bulk_permission_for_non_members(self):
        with self.app.test_client():
            flight_path, operation1 = self._create_operation(flight_path="testflight", user=self.user)
            assert self.fm.is_creator(self.user.id, operation1.id)
            assert self.user.id is not None
            self.fm.add_bulk_permission(operation1.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation1.id)
            # user1 (not a member of operation1) has no right to remove collaboratoruser of operation1 from operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.user1, [self.collaboratoruser.id]) is False
            # collaboratoruser of operation1 has no right to remove user1 (not a member of operation1) from operation1
            assert self.fm.delete_bulk_permission(operation1.id, self.collaboratoruser, [self.user1.id]) is False

    def test_delete_bulk_permission_for_admin_members(self):
        # creator is the one who creates the operation
        # admin is a role to add users.
        # the creator has also this role. But there could be more admins
        # admins have the right to remove themselves
        with self.app.test_client():
            flight_path, operation = self._create_operation(flight_path="saturn")
            assert operation.path == flight_path
            self.fm.add_bulk_permission(operation.id, self.user, [self.adminuser.id], "admin")
            assert self.fm.is_admin(self.adminuser.id, operation.id) is True
            assert self.fm.delete_bulk_permission(operation.id, self.user, [self.user.id]) is False
            assert self.fm.delete_bulk_permission(operation.id, self.adminuser, [self.adminuser.id]) is True

    def test_group_permissions(self):
        with self.app.test_client():
            flight_path_odlo, operation_oslo = self._create_operation(flight_path="flightoslo", category="oslo")

            flight_path_no1, operation_no_1 = self._create_operation(flight_path="flightno1", category="bergen")
            assert self.fm.is_member(self.collaboratoruser.id, operation_no_1.id) is False
            flight_path_group, operation_group = self._create_operation(flight_path="bergenGroup", category="bergen")
            self.fm.add_bulk_permission(operation_group.id, self.user, [self.collaboratoruser.id], "collaborator")
            assert self.fm.is_member(self.collaboratoruser.id, operation_no_1.id) is True
            assert self.fm.is_collaborator(self.collaboratoruser.id, operation_no_1.id)
            # check that not other catergories get changed
            assert self.fm.is_member(self.collaboratoruser.id, operation_oslo.id) is False
            self.fm.modify_bulk_permission(operation_group.id, self.user, [self.collaboratoruser.id], "viewer")
            assert self.fm.is_viewer(self.collaboratoruser.id, operation_no_1.id)
            # now create a new OP with the category bergen and see if our collaborator user has viewer role
            flight_path_no2, operation_no_2 = self._create_operation(flight_path="flightno2", category="bergen")
            assert self.fm.is_viewer(self.collaboratoruser.id, operation_no_2.id)
            # give the user admin role
            self.fm.modify_bulk_permission(operation_group.id, self.user, [self.collaboratoruser.id], "admin")
            assert self.fm.is_admin(self.collaboratoruser.id, operation_no_2.id)
            assert self.fm.is_admin(self.collaboratoruser.id, operation_no_1.id)
            # remove the user
            self.fm.delete_bulk_permission(operation_group.id, self.user, [self.collaboratoruser.id])
            assert self.fm.is_member(self.collaboratoruser.id, operation_group.id) is False

    def test_import_permission(self):
        with self.app.test_client():
            flight_path10, operation10 = self._create_operation(flight_path="operation10")
            flight_path11, operation11 = self._create_operation(flight_path="operation11")
            flight_path12, operation12 = self._create_operation(flight_path="operation12", user=self.anotheruser)
            flight_path13, operation13 = self._create_operation_with_users(flight_path="operation13")
            flight_path14, operation14 = self._create_operation_with_users(flight_path="operation14")
            flight_path15, operation15 = self._create_operation_with_opposite_permissions(flight_path="operation15")
            # equal permissions, nothing to do
            result = (False, None, 'Permissions are already given')
            assert self.fm.import_permissions(operation10.id, operation11.id, self.user.id) == result
            # no admin or creator rights
            result = (False, None, 'Not the creator or admin of this operation')
            assert self.fm.import_permissions(operation10.id, operation12.id, self.user.id) == result
            # not a member
            result = (False, None, 'Not a member of this operation')
            assert self.fm.import_permissions(operation12.id, operation10.id, self.user.id) == result
            # we add to op8 all users of op11
            result = (True, {'add_users': [self.vieweruser.id, self.collaboratoruser.id],
                             'delete_users': [],
                             'modify_users': []}, 'success')
            assert self.fm.import_permissions(operation13.id, operation10.id, self.user.id) == result
            # we remove all users from op8 which are not in op9
            result = (True, {'add_users': [],
                             'delete_users': [self.vieweruser.id, self.collaboratoruser.id],
                             'modify_users': []}, 'success')
            assert self.fm.import_permissions(operation11.id, operation10.id, self.user.id) == result
            # we modify access level
            result = (True, {'add_users': [],
                             'delete_users': [],
                             'modify_users': [self.vieweruser.id, self.collaboratoruser.id]}, 'success')
            assert self.fm.import_permissions(operation15.id, operation14.id, self.user.id) == result

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

    def _create_operation(self, flight_path="firstflight", user=None, content=None, category="default"):
        if user is None:
            user = self.user
        self.fm.create_operation(flight_path, f"info about {flight_path}", user, content=content, category=category)
        operation = Operation.query.filter_by(path=flight_path).first()
        return flight_path, operation

    def _create_operation_with_users(self, flight_path="firstflight", user=None, content=None):
        if user is None:
            user = self.user
        self.fm.create_operation(flight_path, f"info about {flight_path}", user, content=content)
        operation = Operation.query.filter_by(path=flight_path).first()
        self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "viewer")
        self.fm.add_bulk_permission(operation.id, self.user, [self.collaboratoruser.id], "collaborator")
        return flight_path, operation

    def _create_operation_with_opposite_permissions(self, flight_path="firstflight", user=None, content=None):
        if user is None:
            user = self.user
        self.fm.create_operation(flight_path, f"info about {flight_path}", user, content=content)
        operation = Operation.query.filter_by(path=flight_path).first()
        self.fm.add_bulk_permission(operation.id, self.user, [self.vieweruser.id], "collaborator")
        self.fm.add_bulk_permission(operation.id, self.user, [self.collaboratoruser.id], "viewer")
        return flight_path, operation
