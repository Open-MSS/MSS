from PyQt5 import QtCore
from mslib import thermolib
from mslib.msui.qt5.ui_sideview_options import Ui_SideViewOptionsDialog


class Suffix_Module(Ui_SideViewOptionsDialog):
    def verticalunitsclicked(self, index):
        _translate = QtCore.QCoreApplication.translate
        unit = self.cbVerticalAxis.model().itemFromIndex(index)
        currentunit = self.cbVerticalAxis.currentText()
        if unit.text() == "pressure":
            self.sbPbot.setSuffix(_translate("SideViewOptionsDialog", " hpa"))
            self.sbPtop.setSuffix(_translate("SideViewOptionsDialog", " hpa"))
            if currentunit == "pressure altitude":
                self.sbPbot.setValue(thermolib.flightlevel2pressure(self.sbPbot.value() * 32.80) / 100)
                self.sbPtop.setValue(thermolib.flightlevel2pressure(self.sbPtop.value() * 32.80) / 100)
            elif currentunit == "flight level":
                self.sbPbot.setValue(thermolib.flightlevel2pressure(self.sbPbot.value()) / 100)
                self.sbPtop.setValue(thermolib.flightlevel2pressure(self.sbPtop.value()) / 100)
        elif unit.text() == "pressure altitude":
            self.sbPbot.setSuffix(_translate("SideViewOptionsDialog", " km"))
            self.sbPtop.setSuffix(_translate("SideViewOptionsDialog", " km"))
            if currentunit == "pressure":
                self.sbPbot.setValue(thermolib.pressure2flightlevel(self.sbPbot.value() * 100) * 0.03048)
                self.sbPtop.setValue(thermolib.pressure2flightlevel(self.sbPtop.value() * 100) * 0.03048)
            elif currentunit == "flight level":
                self.sbPbot.setValue(self.sbPbot.value() * 0.03048)
                self.sbPtop.setValue(self.sbPtop.value() * 0.03048)
        elif unit.text() == "flight level":
            self.sbPbot.setSuffix(_translate("SideViewOptionsDialog", " hft"))
            self.sbPtop.setSuffix(_translate("SideViewOptionsDialog", " hft"))
            if currentunit == "pressure":
                self.sbPbot.setValue(thermolib.pressure2flightlevel(self.sbPbot.value() * 100))
                self.sbPtop.setValue(thermolib.pressure2flightlevel(self.sbPtop.value() * 100))
            elif currentunit == "pressure altitude":
                self.sbPbot.setValue(self.sbPbot.value() * 32.80)
                self.sbPtop.setValue(self.sbPtop.value() * 32.80)
