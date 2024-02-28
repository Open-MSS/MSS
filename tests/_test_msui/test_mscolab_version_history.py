# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mscolab_version_history
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-operation related gui.

    This file is part of MSS.

    :copyright: Copyright 2020 Tanish Grover
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
import pytest
import mock

from mslib.mscolab.conf import mscolab_settings
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.msui import mscolab
from mslib.msui import msui
from mslib.mscolab.seed import add_user, get_user, add_operation, add_user_to_operation
from mslib.utils.config import modify_config_file


class Test_MscolabVersionHistory:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, mscolab_server):
        self.url = mscolab_server
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.operation_name = "europe"
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_operation(self.operation_name, "test europe")
        assert add_user_to_operation(path=self.operation_name, emailid=self.userdata[0])
        self.user = get_user(self.userdata[0])
        self.window = msui.MSUIMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.create_new_flight_track()
        self.window.show()
        # connect and login to mscolab
        self._connect_to_mscolab(qtbot)
        modify_config_file({"MSS_auth": {self.url: self.userdata[0]}})
        self._login(self.userdata[0], self.userdata[2])
        # activate operation and open chat window
        self._activate_operation_at_index(0)
        self.window.actionVersionHistory.trigger()
        self.version_window = self.window.mscolab.version_window
        assert self.version_window is not None
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.mscolab.logout()
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()

    def test_changes(self, qtbot):
        self._change_version_filter(1)
        len_prev = self.version_window.changes.count()
        # make a changes
        self.window.mscolab.waypoints_model.invert_direction()
        self.window.mscolab.waypoints_model.invert_direction()

        def assert_():
            self.version_window.load_all_changes()
            len_after = self.version_window.changes.count()
            assert len_prev == (len_after - 2)
        qtbot.wait_until(assert_)

    def test_set_version_name(self, qtbot):
        self._set_version_name(qtbot)

    def test_version_name_delete(self, qtbot):
        self._set_version_name(qtbot)
        QtTest.QTest.mouseClick(self.version_window.deleteVersionNameBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert self.version_window.changes.count() == 1
            assert self.version_window.changes.currentItem().version_name is None
        qtbot.wait_until(assert_)

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_undo_changes(self, mockbox, qtbot):
        self._change_version_filter(1)
        assert self.version_window.changes.count() == 0
        # make changes
        for i in range(2):
            self.window.mscolab.waypoints_model.invert_direction()

        def assert_():
            self.version_window.load_all_changes()
            assert self.version_window.changes.count() == 2
        qtbot.wait_until(assert_)
        changes_count = self.version_window.changes.count()
        self._activate_change_at_index(1)
        QtTest.QTest.mouseClick(self.version_window.checkoutBtn, QtCore.Qt.LeftButton)
        new_changes_count = self.version_window.changes.count()
        assert changes_count + 1 == new_changes_count

    def test_refresh(self):
        self._change_version_filter(1)
        changes_count = self.version_window.changes.count()
        self.window.mscolab.waypoints_model.invert_direction()
        self.window.mscolab.waypoints_model.invert_direction()
        QtTest.QTest.mouseClick(self.version_window.refreshBtn, QtCore.Qt.LeftButton)
        new_changes_count = self.version_window.changes.count()
        assert new_changes_count == changes_count + 2

    def _connect_to_mscolab(self, qtbot):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        assert self.connect_window is not None
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)

        def assert_():
            assert not self.connect_window.connectBtn.isVisible()
            assert self.connect_window.disconnectBtn.isVisible()
        qtbot.wait_until(assert_)

    def _login(self, emailid, password):
        assert self.connect_window is not None
        self.connect_window.loginEmailLe.setText(emailid)
        self.connect_window.loginPasswordLe.setText(password)
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)

    def _activate_operation_at_index(self, index):
        assert index < self.window.listOperationsMSC.count()
        item = self.window.listOperationsMSC.item(index)
        point = self.window.listOperationsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.mouseDClick(self.window.listOperationsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)

    def _activate_change_at_index(self, index):
        assert self.version_window is not None
        assert index < self.version_window.changes.count()
        item = self.version_window.changes.item(index)
        point = self.version_window.changes.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.version_window.changes.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtTest.QTest.keyClick(self.version_window.changes.viewport(), QtCore.Qt.Key_Return)

    def _change_version_filter(self, index):
        assert self.version_window is not None
        assert index < self.version_window.versionFilterCB.count()
        self.version_window.versionFilterCB.setCurrentIndex(index)
        self.version_window.versionFilterCB.currentIndexChanged.emit(index)

    def _set_version_name(self, qtbot):
        self._change_version_filter(1)
        num_changes_before = self.version_window.changes.count()
        # make a changes
        self.window.mscolab.waypoints_model.invert_direction()

        # Ensure that the change is visible
        def assert_():
            self.version_window.load_all_changes()
            assert self.version_window.changes.count() == num_changes_before + 1
        qtbot.wait_until(assert_)

        self._activate_change_at_index(0)
        with mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=["MyVersionName", True]):
            QtTest.QTest.mouseClick(self.version_window.nameVersionBtn, QtCore.Qt.LeftButton)

        # Ensure that the name change is fully processed
        def assert_():
            assert self.version_window.changes.currentItem().version_name == "MyVersionName"
        qtbot.wait_until(assert_)
