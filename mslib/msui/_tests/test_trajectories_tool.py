# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_trajectory_tool
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.trajectories_tool

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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
import sys
import mock
from mslib.msui.mss_qt import QtWidgets, QtTest
from mslib._tests.utils import close_modal_messagebox, BASE_DIR
import mslib.msui.trajectories_tool as tt


class Test_TrajectoriesTool(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.listViews = mock.Mock()
        self.listTools = mock.Mock()
        self.listViews.findItems = mock.Mock(side_effect=lambda x, y: [])
        self.listTools.findItems = mock.Mock(side_effect=lambda x, y: [])
        self.window = tt.MSSTrajectoriesToolWindow(listviews=self.listViews, listtools=self.listTools)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_show(self):
        assert True

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getExistingDirectory",
                return_value=os.path.join(sample_path, "trajectories"))
    def test_load_trajectories(self, mockopen):
        self.window.actionOpenTrajectories.trigger()
        assert mockopen.call_count == 1
        assert not close_modal_messagebox(self.window)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QFileDialog.getOpenFileName",
                return_value=os.path.join(sample_path, "nas", "sample.nas"))
    def test_load_nas(self, mockopen):
        self.window.actionOpenFlightTrack.trigger()
        assert mockopen.call_count == 1
        assert not close_modal_messagebox(self.window)
        self.application.exec_()
