# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_merge_waypoints.Test_Save_Merge_Points
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

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
import os
import mock
import pytest
from mslib.msui._tests.test_mscolab_merge_waypoints import Test_Mscolab_Merge_Waypoints
from mslib.msui import flighttrack as ft
from PyQt5 import QtCore, QtTest, QtWidgets


# ToDo Understand why this needs to be skipped, it runs when direct called
@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Save_Merge_Points(Test_Mscolab_Merge_Waypoints):
    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_save_merge_points(self, mockbox):
        pytest.skip("probably a timing problem, fails sometimes")
        self.emailid = "mergepoints@alpha.org"
        self._create_user_data(emailid=self.emailid)
        self.window.workLocallyCheckBox.setChecked(True)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.window.waypoints_model.invert_direction()
        merge_waypoints_model = None

        def handle_merge_dialog():
            nonlocal merge_waypoints_model
            self._select_waypoints(self.window.merge_dialog.localWaypointsTable)
            self._select_waypoints(self.window.merge_dialog.serverWaypointsTable)
            merge_waypoints_model = self.window.merge_dialog.merge_waypoints_model
            assert merge_waypoints_model is not None
            QtTest.QTest.mouseClick(self.window.merge_dialog.saveBtn, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(100)

        QtCore.QTimer.singleShot(3000, handle_merge_dialog)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton, delay=1)
        QtWidgets.QApplication.processEvents()
        # get the updated waypoints model from the server
        # ToDo understand why requesting in follow up test of self.window.waypoints_model not working
        server_xml = self.window.request_wps_from_server()
        server_waypoints_model = ft.WaypointsTableModel(xml_content=server_xml)
        new_local_wp = server_waypoints_model
        new_wp_count = len(merge_waypoints_model.waypoints)
        assert new_wp_count == 4
        assert len(new_local_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_local_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
        self.window.workLocallyCheckBox.setChecked(False)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_server_wp = self.window.waypoints_model
        assert len(new_server_wp.waypoints) == new_wp_count
        for wp_index in range(new_wp_count):
            assert new_server_wp.waypoint_data(wp_index).lat == merge_waypoints_model.waypoint_data(wp_index).lat
