#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    mslib.msui.mss
    ~~~~~~~~~~~~~~~

    Mission Support System Python/Qt Rename Message

    Message to inform the user of the rename from mss to msui.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

from mslib.msui.qt5 import ui_mss_rename_message as ui
from PyQt5 import QtWidgets


class MSSMainWindow(QtWidgets.QMainWindow, ui.Ui_MSSMainWindow):
    def __init__(self, *args):
        super().__init__(*args)
        self.setupUi(self)


def main():
    application = QtWidgets.QApplication(sys.argv)
    application.setApplicationDisplayName("MSS")
    mainwindow = MSSMainWindow()
    mainwindow.show()
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
