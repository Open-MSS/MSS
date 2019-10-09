# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_add_user.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_addUserDialog(object):
    def setupUi(self, addUserDialog):
        addUserDialog.setObjectName("addUserDialog")
        addUserDialog.resize(413, 275)
        self.buttonBox = QtWidgets.QDialogButtonBox(addUserDialog)
        self.buttonBox.setGeometry(QtCore.QRect(100, 230, 301, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(addUserDialog)
        self.label.setGeometry(QtCore.QRect(90, 80, 59, 15))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(addUserDialog)
        self.label_2.setGeometry(QtCore.QRect(78, 110, 71, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(addUserDialog)
        self.label_3.setGeometry(QtCore.QRect(30, 140, 111, 20))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(addUserDialog)
        self.label_4.setGeometry(QtCore.QRect(60, 170, 81, 20))
        self.label_4.setObjectName("label_4")
        self.emailid = QtWidgets.QLineEdit(addUserDialog)
        self.emailid.setGeometry(QtCore.QRect(150, 80, 211, 23))
        self.emailid.setObjectName("emailid")
        self.password = QtWidgets.QLineEdit(addUserDialog)
        self.password.setGeometry(QtCore.QRect(150, 110, 141, 23))
        self.password.setObjectName("password")
        self.rePassword = QtWidgets.QLineEdit(addUserDialog)
        self.rePassword.setGeometry(QtCore.QRect(150, 140, 141, 23))
        self.rePassword.setObjectName("rePassword")
        self.username = QtWidgets.QLineEdit(addUserDialog)
        self.username.setGeometry(QtCore.QRect(150, 170, 141, 23))
        self.username.setObjectName("username")

        self.retranslateUi(addUserDialog)
        self.buttonBox.accepted.connect(addUserDialog.accept)
        self.buttonBox.rejected.connect(addUserDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addUserDialog)

    def retranslateUi(self, addUserDialog):
        _translate = QtCore.QCoreApplication.translate
        addUserDialog.setWindowTitle(_translate("addUserDialog", "Add user"))
        self.label.setText(_translate("addUserDialog", "emailid"))
        self.label_2.setText(_translate("addUserDialog", "password"))
        self.label_3.setText(_translate("addUserDialog", "reenter password"))
        self.label_4.setText(_translate("addUserDialog", "username"))

