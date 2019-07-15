# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab
    ~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

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
import logging
import multiprocessing
import time

from mslib.mscolab.server import db, sockio, app
import mslib.msui.mscolab as mc


class Test_Mscolab(object):
    def setup(self):
        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mc.MSSMscolabWindow()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

        # start mscolab server
        self._app = app
        db.init_app(self._app)
        self.p = multiprocessing.Process(
            target=sockio.run,
            args=(app,),
            kwargs={'port': 8083})
        self.p.start()
        time.sleep(1)

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        # close mscolab server
        self.p.terminate()

    def test_login(self):
        # login
        self.window.emailid.setText('a')
        self.window.password.setText('a')
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        # screen shows logout button
        assert self.window.loggedInWidget.isVisible() is True
        assert self.window.loginWidget.isVisible() is False
        # test project listing visibility
        # test logout
        QtTest.QTest.mouseClick(self.window.logoutButton, QtCore.Qt.LeftButton)
        assert self.window.loggedInWidget.isVisible() is False
        assert self.window.loginWidget.isVisible() is True
        logging.debug("done")
