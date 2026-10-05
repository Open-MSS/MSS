# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_capabilities

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2026 by the MSS team, see AUTHORS.
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

    def start_window(self):
        self.window = wc.WMSCapabilitiesBrowser(
            url="http://example.com",
            capabilities=self.capabilities)
        QtTest.QTest.qWaitForWindowExposed(self.window)

    def test_window_start(self):
        self.start_window()

    def test_window_contact_none(self):
        self.capabilities.provider.contact = None
        self.start_window()

    def test_switch_view(self):
        self.start_window()
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.cbFullView, QtCore.Qt.LeftButton)

    def test_wms_strings_are_text(self):
        # title, abstract and contact come from the WMS server, an <img> in them must not be loaded
        markup = '<img src="file://attacker.example/share/x.png"><a href="file:///etc/passwd">link</a>'
        self.capabilities.identification.title = f"Title {markup}"
        self.capabilities.identification.abstract = f"Abstract {markup}"
        self.capabilities.identification.type = "OGC:WMS"
        self.capabilities.identification.version = "1.3.0"
        self.capabilities.identification.keywords = [markup]
        self.capabilities.identification.accessconstraints = markup
        self.capabilities.identification.fees = markup
        self.capabilities.provider.contact.name = f"Name {markup}"
        self.capabilities.provider.contact.email = "<b>wms@example.org</b>"
        self.window = wc.WMSCapabilitiesBrowser(url=f"https://wms.example/{markup}", capabilities=self.capabilities)
        text = self.window.txtCapabilities.toPlainText()
        assert f"Title: Title {markup}" in text
        assert f"Abstract {markup}" in text
        assert f"Name {markup}" in text
        assert "<b>wms@example.org</b>" in text
        assert f"Fees: {markup}" in text
        html = self.window.txtCapabilities.toHtml()
        assert "<img" not in html and "<a " not in html
        assert self.window.lblURL.textFormat() == QtCore.Qt.PlainText
        assert self.window.lblURL.text() == f"https://wms.example/{markup}"
