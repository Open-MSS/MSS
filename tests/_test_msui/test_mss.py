# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_mss
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.mss

    This file is part of MSS.

    :copyright: Copyright 2022 Joern Ungermann
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


import sys
from PyQt5 import QtWidgets, QtTest, QtCore
from mslib.msui import mss


def test_mss_rename_message():
    application = QtWidgets.QApplication(sys.argv)
    main_window = mss.MSSMainWindow()
    main_window.show()
    QtTest.QTest.mouseClick(main_window.pushButton, QtCore.Qt.LeftButton)
    QtWidgets.QApplication.processEvents()
    application.quit()
    QtWidgets.QApplication.processEvents()
