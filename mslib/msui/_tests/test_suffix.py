import sys
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
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
        k = self.window.cbVerticalAxis.view()
        suffix = [' hpa', ' km', ' hft']
        for i in range(len(suffix)):
            index = k.model().index(i, 0)
            k.scrollTo(index)
            item_react = k.visualRect(index)
            QtTest.QTest.mouseClick(k.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, item_react.center())
            QtWidgets.QApplication.processEvents()
            assert self.window.sbPtop.suffix() == suffix[i]
