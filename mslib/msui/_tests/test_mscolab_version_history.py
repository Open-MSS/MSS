# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_version_history
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

    This file is part of mss.

    :copyright: Copyright 2020 Tanish Grover
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
import os
import sys
import pytest
import mock

from mslib._tests.utils import mscolab_start_server
from mslib.mscolab.conf import mscolab_settings
from PyQt5 import QtCore, QtTest, QtWidgets
from mslib.msui import mscolab
import mslib.msui.mss_pyui as mss_pyui


PORTS = list(range(9591, 9620))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_MscolabVersionHistory(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        self.window.show()
        # connect and login to mscolab
        self._connect_to_mscolab()
        self._login()
        # activate project and open chat window
        self._activate_project_at_index(0)
        self.window.actionVersionHistory.trigger()
        QtWidgets.QApplication.processEvents()
        self.version_window = self.window.mscolab.version_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_changes(self):
        self._change_version_filter(1)
        len_prev = self.version_window.changes.count()
        # make a changes
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        len_after = self.version_window.changes.count()
        assert len_prev == (len_after - 2)

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=["MyVersionName", True])
    def test_set_version_name(self, mockbox):
        self._change_version_filter(1)
        # make a changes
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        self._activate_change_at_index(0)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.version_window.nameVersionBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert self.version_window.changes.currentItem().version_name == "MyVersionName"
        assert self.version_window.changes.count() == 1

    def test_version_name_delete(self):
        self._activate_change_at_index(0)
        QtTest.QTest.mouseClick(self.version_window.deleteVersionNameBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        assert self.version_window.changes.count() == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_undo(self, mockbox):
        self._change_version_filter(1)
        # make changes
        for i in range(2):
            self.window.mscolab.waypoints_model.invert_direction()
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(100)
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        changes_count = self.version_window.changes.count()
        self._activate_change_at_index(1)
        QtTest.QTest.mouseClick(self.version_window.checkoutBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(200)
        new_changes_count = self.version_window.changes.count()
        assert changes_count + 1 == new_changes_count

    def test_refresh(self):
        self._change_version_filter(1)
        changes_count = self.version_window.changes.count()
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        self.window.mscolab.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        QtTest.QTest.mouseClick(self.version_window.refreshBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
        new_changes_count = self.version_window.changes.count()
        assert new_changes_count == changes_count + 2

    def _connect_to_mscolab(self):
        self.connect_window = mscolab.MSColab_ConnectDialog(parent=self.window, mscolab=self.window.mscolab)
        self.window.mscolab.connect_window = self.connect_window
        self.connect_window.urlCb.setEditText(self.url)
        self.connect_window.show()
        QtTest.QTest.mouseClick(self.connect_window.connectBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _login(self):
        self.connect_window.loginEmailLe.setText('a')
        self.connect_window.loginPasswordLe.setText('a')
        QtTest.QTest.mouseClick(self.connect_window.loginBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(500)

    def _activate_project_at_index(self, index):
        item = self.window.listProjectsMSC.item(index)
        point = self.window.listProjectsMSC.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjectsMSC.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _activate_change_at_index(self, index):
        item = self.version_window.changes.item(index)
        point = self.version_window.changes.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.version_window.changes.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClick(self.version_window.changes.viewport(), QtCore.Qt.Key_Return)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)

    def _change_version_filter(self, index):
        self.version_window.versionFilterCB.setCurrentIndex(index)
        self.version_window.versionFilterCB.currentIndexChanged.emit(index)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(100)
