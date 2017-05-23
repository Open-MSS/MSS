# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_wms_password_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from builtins import object
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WMSAuthenticationDialog(object):
    def setupUi(self, WMSAuthenticationDialog):
        WMSAuthenticationDialog.setObjectName("WMSAuthenticationDialog")
        WMSAuthenticationDialog.resize(493, 151)
        self.verticalLayout = QtWidgets.QVBoxLayout(WMSAuthenticationDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblMessage = QtWidgets.QLabel(WMSAuthenticationDialog)
        font = QtGui.QFont()
        font.setItalic(True)
        self.lblMessage.setFont(font)
        self.lblMessage.setObjectName("lblMessage")
        self.verticalLayout.addWidget(self.lblMessage)
        self.label = QtWidgets.QLabel(WMSAuthenticationDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(WMSAuthenticationDialog)
        self.label_2.setMinimumSize(QtCore.QSize(80, 0))
        self.label_2.setMaximumSize(QtCore.QSize(80, 16777215))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.leUsername = QtWidgets.QLineEdit(WMSAuthenticationDialog)
        self.leUsername.setObjectName("leUsername")
        self.horizontalLayout.addWidget(self.leUsername)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(WMSAuthenticationDialog)
        self.label_3.setMinimumSize(QtCore.QSize(80, 0))
        self.label_3.setMaximumSize(QtCore.QSize(80, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lePassword = QtWidgets.QLineEdit(WMSAuthenticationDialog)
        self.lePassword.setInputMask("")
        self.lePassword.setText("")
        self.lePassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lePassword.setObjectName("lePassword")
        self.horizontalLayout_2.addWidget(self.lePassword)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(WMSAuthenticationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(WMSAuthenticationDialog)
        self.buttonBox.accepted.connect(WMSAuthenticationDialog.accept)
        self.buttonBox.rejected.connect(WMSAuthenticationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(WMSAuthenticationDialog)

    def retranslateUi(self, WMSAuthenticationDialog):
        _translate = QtCore.QCoreApplication.translate
        WMSAuthenticationDialog.setWindowTitle(_translate("WMSAuthenticationDialog", "HTTP Authentication"))
        self.lblMessage.setText(_translate("WMSAuthenticationDialog", "Web Map Service"))
        self.label.setText(_translate("WMSAuthenticationDialog", "The server you are trying to connect requires a username and a password:"))
        self.label_2.setText(_translate("WMSAuthenticationDialog", "User name:"))
        self.label_3.setText(_translate("WMSAuthenticationDialog", "Password:"))

