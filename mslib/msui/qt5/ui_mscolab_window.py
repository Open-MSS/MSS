# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mscolab_window.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MSSMscolabWindow(object):
    def setupUi(self, MSSMscolabWindow):
        MSSMscolabWindow.setObjectName("MSSMscolabWindow")
        MSSMscolabWindow.resize(480, 640)
        self.pushButton = QtWidgets.QPushButton(MSSMscolabWindow)
        self.pushButton.setGeometry(QtCore.QRect(170, 20, 80, 23))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(MSSMscolabWindow)
        QtCore.QMetaObject.connectSlotsByName(MSSMscolabWindow)

    def retranslateUi(self, MSSMscolabWindow):
        _translate = QtCore.QCoreApplication.translate
        MSSMscolabWindow.setWindowTitle(_translate("MSSMscolabWindow", "MSS Colab Window"))
        self.pushButton.setText(_translate("MSSMscolabWindow", "login"))

