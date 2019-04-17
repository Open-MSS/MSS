import mock
import os
import shutil
import sys
import paste
import paste.httpserver
import multiprocessing
import tempfile
import mslib.mswms.wms
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore, QtGui
from mslib.msui import flighttrack as ft
import mslib.msui.sideview as tv

class Test_MSS_SV_OptionsDialog(object):
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
        
        self.window.verticalunitsclicked(1)
        QtWidgets.QApplication.processEvents()
        assert self.window.sbPtop.suffix() == " hpa"