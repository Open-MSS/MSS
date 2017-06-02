# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'msui/ui_performance_settings.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_PerformanceSettingsDialog(object):
    def setupUi(self, PerformanceSettingsDialog):
        PerformanceSettingsDialog.setObjectName(_fromUtf8("PerformanceSettingsDialog"))
        PerformanceSettingsDialog.resize(319, 241)
        self.buttonBox = QtGui.QDialogButtonBox(PerformanceSettingsDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 200, 271, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.dteTakeoffTime = QtGui.QDateTimeEdit(PerformanceSettingsDialog)
        self.dteTakeoffTime.setGeometry(QtCore.QRect(160, 100, 141, 22))
        self.dteTakeoffTime.setObjectName(_fromUtf8("dteTakeoffTime"))
        self.label = QtGui.QLabel(PerformanceSettingsDialog)
        self.label.setGeometry(QtCore.QRect(20, 100, 91, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.dsbTakeoffWeight = QtGui.QDoubleSpinBox(PerformanceSettingsDialog)
        self.dsbTakeoffWeight.setGeometry(QtCore.QRect(160, 130, 141, 22))
        self.dsbTakeoffWeight.setDecimals(0)
        self.dsbTakeoffWeight.setMaximum(9999999.0)
        self.dsbTakeoffWeight.setSingleStep(1000.0)
        self.dsbTakeoffWeight.setObjectName(_fromUtf8("dsbTakeoffWeight"))
        self.dsbFuel = QtGui.QDoubleSpinBox(PerformanceSettingsDialog)
        self.dsbFuel.setGeometry(QtCore.QRect(160, 160, 141, 22))
        self.dsbFuel.setDecimals(0)
        self.dsbFuel.setMaximum(9999999.0)
        self.dsbFuel.setSingleStep(1000.0)
        self.dsbFuel.setObjectName(_fromUtf8("dsbFuel"))
        self.label_2 = QtGui.QLabel(PerformanceSettingsDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 130, 121, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(PerformanceSettingsDialog)
        self.label_3.setGeometry(QtCore.QRect(20, 160, 101, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.cbShowPerformance = QtGui.QCheckBox(PerformanceSettingsDialog)
        self.cbShowPerformance.setGeometry(QtCore.QRect(20, 20, 141, 20))
        self.cbShowPerformance.setObjectName(_fromUtf8("cbShowPerformance"))
        self.pbLoadPerformance = QtGui.QPushButton(PerformanceSettingsDialog)
        self.pbLoadPerformance.setGeometry(QtCore.QRect(210, 50, 93, 28))
        self.pbLoadPerformance.setObjectName(_fromUtf8("pbLoadPerformance"))
        self.lbAircraftName = QtGui.QLabel(PerformanceSettingsDialog)
        self.lbAircraftName.setGeometry(QtCore.QRect(80, 60, 121, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.lbAircraftName.setFont(font)
        self.lbAircraftName.setObjectName(_fromUtf8("lbAircraftName"))
        self.label_5 = QtGui.QLabel(PerformanceSettingsDialog)
        self.label_5.setGeometry(QtCore.QRect(20, 60, 51, 16))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_5.setFont(font)
        self.label_5.setObjectName(_fromUtf8("label_5"))

        self.retranslateUi(PerformanceSettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PerformanceSettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PerformanceSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PerformanceSettingsDialog)

    def retranslateUi(self, PerformanceSettingsDialog):
        PerformanceSettingsDialog.setWindowTitle(_translate("PerformanceSettingsDialog", "PerformanceSettingsDialog", None))
        self.label.setText(_translate("PerformanceSettingsDialog", "Take off time", None))
        self.label_2.setText(_translate("PerformanceSettingsDialog", "Takeoff weight (lb)", None))
        self.label_3.setText(_translate("PerformanceSettingsDialog", "Fuel (lb)", None))
        self.cbShowPerformance.setText(_translate("PerformanceSettingsDialog", "Show Performance", None))
        self.pbLoadPerformance.setText(_translate("PerformanceSettingsDialog", "Load", None))
        self.lbAircraftName.setText(_translate("PerformanceSettingsDialog", "Dummy", None))
        self.label_5.setText(_translate("PerformanceSettingsDialog", "Aircraft:", None))

