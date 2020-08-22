# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_add_user.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_addUserDialog(object):
    def setupUi(self, addUserDialog):
        addUserDialog.setObjectName("addUserDialog")
        addUserDialog.resize(375, 232)
        self.gridLayout = QtWidgets.QGridLayout(addUserDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setVerticalSpacing(14)
        self.formLayout.setObjectName("formLayout")
        self.username = QtWidgets.QLineEdit(addUserDialog)
        self.username.setObjectName("username")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.username)
        self.emailid = QtWidgets.QLineEdit(addUserDialog)
        self.emailid.setObjectName("emailid")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.emailid)
        self.passwordLabel = QtWidgets.QLabel(addUserDialog)
        self.passwordLabel.setObjectName("passwordLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.passwordLabel)
        self.password = QtWidgets.QLineEdit(addUserDialog)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setObjectName("password")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.password)
        self.confirmPasswordLabel = QtWidgets.QLabel(addUserDialog)
        self.confirmPasswordLabel.setObjectName("confirmPasswordLabel")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.confirmPasswordLabel)
        self.rePassword = QtWidgets.QLineEdit(addUserDialog)
        self.rePassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.rePassword.setObjectName("rePassword")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.rePassword)
        self.emailIDLabel = QtWidgets.QLabel(addUserDialog)
        self.emailIDLabel.setObjectName("emailIDLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.emailIDLabel)
        self.usernameLabel = QtWidgets.QLabel(addUserDialog)
        self.usernameLabel.setObjectName("usernameLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.usernameLabel)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(addUserDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(addUserDialog)
        self.buttonBox.accepted.connect(addUserDialog.accept)
        self.buttonBox.rejected.connect(addUserDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addUserDialog)

    def retranslateUi(self, addUserDialog):
        _translate = QtCore.QCoreApplication.translate
        addUserDialog.setWindowTitle(_translate("addUserDialog", "Add user"))
        self.username.setPlaceholderText(_translate("addUserDialog", "John Doe"))
        self.emailid.setPlaceholderText(_translate("addUserDialog", "johndoe@gmail.com"))
        self.passwordLabel.setText(_translate("addUserDialog", "Password:"))
        self.password.setPlaceholderText(_translate("addUserDialog", "Your password"))
        self.confirmPasswordLabel.setText(_translate("addUserDialog", "Confirm Password:"))
        self.rePassword.setPlaceholderText(_translate("addUserDialog", "Confirm your password"))
        self.emailIDLabel.setText(_translate("addUserDialog", "Email:"))
        self.usernameLabel.setText(_translate("addUserDialog", "Username:"))

