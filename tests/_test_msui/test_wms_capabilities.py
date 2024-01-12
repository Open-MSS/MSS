# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_capabilities

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2024 by the MSS team, see AUTHORS.
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
import pytest

from PyQt5 import QtTest, QtCore
import mslib.msui.wms_capabilities as wc


class Test_WMSCapabilities:

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
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
        yield

    def start_window(self, qtbot):
        self.window = wc.WMSCapabilitiesBrowser(
            url="http://example.com",
            capabilities=self.capabilities)
        qtbot.add_widget(self.window)
        QtTest.QTest.qWaitForWindowExposed(self.window)

    def test_window_start(self, qtbot):
        self.start_window(qtbot)

    def test_window_contact_none(self, qtbot):
        self.capabilities.provider.contact = None
        self.start_window(qtbot)

    def test_switch_view(self, qtbot):
        self.start_window(qtbot)
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
