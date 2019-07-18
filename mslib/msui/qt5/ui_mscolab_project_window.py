# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mscolab_project_window.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(907, 601)
        self.username = QtWidgets.QLineEdit(Form)
        self.username.setGeometry(QtCore.QRect(10, 20, 113, 23))
        self.username.setObjectName("username")
        self.accessLevel = QtWidgets.QComboBox(Form)
        self.accessLevel.setGeometry(QtCore.QRect(130, 20, 101, 23))
        self.accessLevel.setObjectName("accessLevel")
        self.accessLevel.addItem("")
        self.accessLevel.addItem("")
        self.accessLevel.addItem("")
        self.add = QtWidgets.QPushButton(Form)
        self.add.setGeometry(QtCore.QRect(240, 20, 41, 23))
        self.add.setObjectName("add")
        self.modify = QtWidgets.QPushButton(Form)
        self.modify.setGeometry(QtCore.QRect(290, 20, 51, 23))
        self.modify.setObjectName("modify")
        self.verticalLayoutWidget = QtWidgets.QWidget(Form)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 70, 191, 114))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.collaboratorsList = QtWidgets.QListView(self.verticalLayoutWidget)
        self.collaboratorsList.setObjectName("collaboratorsList")
        self.verticalLayout_4.addWidget(self.collaboratorsList)
        self.delete_1 = QtWidgets.QPushButton(Form)
        self.delete_1.setGeometry(QtCore.QRect(350, 20, 51, 23))
        self.delete_1.setObjectName("delete_1")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.accessLevel.setItemText(0, _translate("Form", "collaborator"))
        self.accessLevel.setItemText(1, _translate("Form", "admin"))
        self.accessLevel.setItemText(2, _translate("Form", "viewer"))
        self.add.setText(_translate("Form", "add"))
        self.modify.setText(_translate("Form", "modify"))
        self.delete_1.setText(_translate("Form", "delete"))

