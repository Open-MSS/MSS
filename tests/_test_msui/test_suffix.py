# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_suffix
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest function to test msui.sideview method
    'verticalunitsclicked' for change of suffix

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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
from PyQt5 import QtWidgets, QtTest
import mslib.msui.sideview as tv


class Test_SuffixChange(object):
    def setup_method(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = tv.MSUI_SV_OptionsDialog()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown_method(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_suffixchange(self):
        suffix = [' hPa', ' km', ' hft']
        for i in range(len(suffix)):
            self.window.cbVerticalAxis.setCurrentIndex(i)
            QtWidgets.QApplication.processEvents()
            assert self.window.sbPtop.suffix() == suffix[i]
