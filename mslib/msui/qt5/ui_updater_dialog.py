# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_updater_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Updater(object):
    def setupUi(self, Updater):
        Updater.setObjectName("Updater")
        Updater.setWindowModality(QtCore.Qt.ApplicationModal)
        Updater.resize(854, 353)
        self.verticalLayout = QtWidgets.QVBoxLayout(Updater)
        self.verticalLayout.setObjectName("verticalLayout")
        self.statusLabel = QtWidgets.QLabel(Updater)
        self.statusLabel.setObjectName("statusLabel")
        self.verticalLayout.addWidget(self.statusLabel)
        self.output = QtWidgets.QPlainTextEdit(Updater)
        self.output.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.output.setReadOnly(True)
        self.output.setCenterOnScroll(False)
        self.output.setObjectName("output")
        self.verticalLayout.addWidget(self.output)

        self.retranslateUi(Updater)
        QtCore.QMetaObject.connectSlotsByName(Updater)

    def retranslateUi(self, Updater):
        _translate = QtCore.QCoreApplication.translate
        Updater.setWindowTitle(_translate("Updater", "Updater"))
        self.statusLabel.setText(_translate("Updater", "Status"))
