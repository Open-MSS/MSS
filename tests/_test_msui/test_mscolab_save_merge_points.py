# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_merge_waypoints.Test_Save_Merge_Points
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-operation related gui.

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
import mock
from tests._test_msui.test_mscolab_merge_waypoints import Test_Mscolab_Merge_Waypoints
from mslib.msui import flighttrack as ft
from PyQt5 import QtCore, QtTest


class Test_Save_Merge_Points(Test_Mscolab_Merge_Waypoints):
    def test_save_merge_points(self, qtbot):
        self.emailid = "mergepoints@alpha.org"
        self._create_user_data(qtbot, emailid=self.emailid)
        self.window.workLocallyCheckbox.setChecked(True)
        self.window.mscolab.waypoints_model.invert_direction()
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            self._select_waypoints(self.window.mscolab.merge_dialog.localWaypointsTable)
            self._select_waypoints(self.window.mscolab.merge_dialog.serverWaypointsTable)
            merge_waypoints_model = self.window.mscolab.merge_dialog.merge_waypoints_model
            QtTest.QTest.mouseClick(self.window.mscolab.merge_dialog.saveBtn, QtCore.Qt.LeftButton)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        # QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        # trigger save to server action from server options combobox
        with mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
            self.window.serverOptionsCb.setCurrentIndex(2)
            m.assert_called_once()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test of self.window.waypoints_model not working
        server_xml = self.window.mscolab.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
        self.window.workLocallyCheckbox.setChecked(False)
        new_server_wp = self.window.mscolab.waypoints_model
        assert len(new_server_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_server_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
