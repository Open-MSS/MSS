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
        Updater.setWindowModality(QtCore.Qt.NonModal)
        Updater.resize(854, 338)
        self.verticalLayout = QtWidgets.QVBoxLayout(Updater)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.labelVersion = QtWidgets.QLabel(Updater)
        self.labelVersion.setObjectName("labelVersion")
        self.horizontalLayout.addWidget(self.labelVersion)
        self.btUpdate = QtWidgets.QPushButton(Updater)
        self.btUpdate.setEnabled(False)
        self.btUpdate.setObjectName("btUpdate")
        self.horizontalLayout.addWidget(self.btUpdate)
        self.btRestart = QtWidgets.QPushButton(Updater)
        self.btRestart.setEnabled(False)
        self.btRestart.setObjectName("btRestart")
        self.horizontalLayout.addWidget(self.btRestart)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(Updater)
        self.label.setOpenExternalLinks(True)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.statusLabel = QtWidgets.QLabel(Updater)
        self.statusLabel.setObjectName("statusLabel")
        self.verticalLayout.addWidget(self.statusLabel)
        self.output = QtWidgets.QPlainTextEdit(Updater)
        font = QtGui.QFont()
        font.setFamily("Sans Serif")
        font.setStyleStrategy(QtGui.QFont.PreferDefault)
        self.output.setFont(font)
        self.output.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.output.setReadOnly(True)
        self.output.setPlainText("")
        self.output.setCenterOnScroll(False)
        self.output.setObjectName("output")
        self.verticalLayout.addWidget(self.output)

        self.retranslateUi(Updater)
        QtCore.QMetaObject.connectSlotsByName(Updater)

    def retranslateUi(self, Updater):
        _translate = QtCore.QCoreApplication.translate
        Updater.setWindowTitle(_translate("Updater", "Updater"))
        self.labelVersion.setText(_translate("Updater", "Newest Version: x.x.x"))
        self.btUpdate.setText(_translate("Updater", "Update"))
        self.btRestart.setText(_translate("Updater", "Restart MSS"))
        self.label.setText(_translate("Updater", "<html><head/><body><p><a href=\"https://mss.readthedocs.io/en/stable/installation.html#install\"><span style=\" text-decoration: underline; color:#0000ff;\">Manual update instructions</span></a></p></body></html>"))
        self.statusLabel.setText(_translate("Updater", "Nothing to do"))
