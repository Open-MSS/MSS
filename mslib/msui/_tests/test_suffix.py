# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_suffix
    ~~~~~~~~~~~~~~~~~~~

    Side view module of the msui

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
import mslib.msui.sideview as tv


class Test_SuffixChange(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = tv.MSS_SV_OptionsDialog()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_suffixchange(self):
        cbView = self.window.cbVerticalAxis.view()
        suffix = [' hpa', ' km', ' hft']
        for i in range(len(suffix)):
            index = cbView.model().index(i, 0)
            cbView.scrollTo(index)
            item_react = cbView.visualRect(index)
            QtTest.QTest.mouseClick(cbView.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item_react.center())
            QtWidgets.QApplication.processEvents()
            assert self.window.sbPtop.suffix() == suffix[i]
