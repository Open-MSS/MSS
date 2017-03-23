# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_capabilities

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


import sys
import mock
import os

from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
from mslib._tests.utils import close_modal_messagebox
import mslib.msui.wms_capabilities as wc


class Test_WMSCapabilities(object):

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.capabilities = mock.Mock()
        self.capabilities.capabilities_document = "Holla die Waldfee"
        self.capabilities.provider = mock.Mock()
        self.capabilities.identification = mock.Mock()

        self.window = wc.WMSCapabilitiesBrowser(
            url="http://example.com",
            capabilities=self.capabilities)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_window_start(self):
        assert not close_modal_messagebox(self.window)

    def test_switch_view(self):
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert not close_modal_messagebox(self.window)
