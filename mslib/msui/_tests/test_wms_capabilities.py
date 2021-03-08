# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_capabilities

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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

from PyQt5 import QtWidgets, QtTest, QtCore
import mslib.msui.wms_capabilities as wc


class Test_WMSCapabilities(object):

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.capabilities = mock.Mock()
        self.capabilities.capabilities_document = u"Hölla die Waldfee".encode("utf-8")
        self.capabilities.provider = mock.Mock()
        self.capabilities.identification = mock.Mock()
        self.capabilities.provider.contact = mock.Mock()
        self.capabilities.provider.contact.name = None
        self.capabilities.provider.contact.organization = None
        self.capabilities.provider.contact.email = None
        self.capabilities.provider.contact.address = None
        self.capabilities.provider.contact.postcode = None
        self.capabilities.provider.contact.city = None

    def start_window(self):
        self.window = wc.WMSCapabilitiesBrowser(
            url="http://example.com",
            capabilities=self.capabilities)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_window_start(self, mockbox):
        self.start_window()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_window_contact_none(self, mockbox):
        self.capabilities.provider.contact = None
        self.start_window()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_switch_view(self, mockbox):
        self.start_window()
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
