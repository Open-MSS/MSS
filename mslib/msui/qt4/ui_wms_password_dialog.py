# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_wms_password_dialog.ui'
#
# Created: Thu Mar 17 17:15:11 2011
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!

from builtins import object
from PyQt4 import QtCore, QtGui


class Ui_WMSAuthenticationDialog(object):
    def setupUi(self, WMSAuthenticationDialog):
        WMSAuthenticationDialog.setObjectName("WMSAuthenticationDialog")
        WMSAuthenticationDialog.resize(493, 151)
        self.verticalLayout = QtGui.QVBoxLayout(WMSAuthenticationDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblMessage = QtGui.QLabel(WMSAuthenticationDialog)
        font = QtGui.QFont()
        font.setItalic(True)
        self.lblMessage.setFont(font)
        self.lblMessage.setObjectName("lblMessage")
        self.verticalLayout.addWidget(self.lblMessage)
        self.label = QtGui.QLabel(WMSAuthenticationDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtGui.QLabel(WMSAuthenticationDialog)
        self.label_2.setMinimumSize(QtCore.QSize(80, 0))
        self.label_2.setMaximumSize(QtCore.QSize(80, 16777215))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.leUsername = QtGui.QLineEdit(WMSAuthenticationDialog)
        self.leUsername.setObjectName("leUsername")
        self.horizontalLayout.addWidget(self.leUsername)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtGui.QLabel(WMSAuthenticationDialog)
        self.label_3.setMinimumSize(QtCore.QSize(80, 0))
        self.label_3.setMaximumSize(QtCore.QSize(80, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lePassword = QtGui.QLineEdit(WMSAuthenticationDialog)
        self.lePassword.setEchoMode(QtGui.QLineEdit.Password)
        self.lePassword.setObjectName("lePassword")
        self.horizontalLayout_2.addWidget(self.lePassword)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(WMSAuthenticationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(WMSAuthenticationDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), WMSAuthenticationDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), WMSAuthenticationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(WMSAuthenticationDialog)

    def retranslateUi(self, WMSAuthenticationDialog):
        WMSAuthenticationDialog.setWindowTitle(
            QtGui.QApplication.translate("WMSAuthenticationDialog", "HTTP Authentication", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.lblMessage.setText(QtGui.QApplication.translate("WMSAuthenticationDialog", "Web Map Service", None,
                                                             QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("WMSAuthenticationDialog",
                                                        "The server you are trying to connect requires a "
                                                        "username and a password:",
                                                        None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(
            QtGui.QApplication.translate("WMSAuthenticationDialog", "User name:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(
            QtGui.QApplication.translate("WMSAuthenticationDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))
