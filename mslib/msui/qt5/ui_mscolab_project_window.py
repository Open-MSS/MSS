# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_project_window.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MscolabProject(object):
    def setupUi(self, MscolabProject):
        MscolabProject.setObjectName("MscolabProject")
        MscolabProject.resize(905, 601)
        self.username = QtWidgets.QLineEdit(MscolabProject)
        self.username.setGeometry(QtCore.QRect(10, 20, 113, 23))
        self.username.setObjectName("username")
        self.accessLevel = QtWidgets.QComboBox(MscolabProject)
        self.accessLevel.setGeometry(QtCore.QRect(130, 20, 101, 23))
        self.accessLevel.setObjectName("accessLevel")
        self.accessLevel.addItem("")
        self.accessLevel.addItem("")
        self.accessLevel.addItem("")
        self.add = QtWidgets.QPushButton(MscolabProject)
        self.add.setGeometry(QtCore.QRect(240, 20, 41, 23))
        self.add.setObjectName("add")
        self.modify = QtWidgets.QPushButton(MscolabProject)
        self.modify.setGeometry(QtCore.QRect(290, 20, 51, 23))
        self.modify.setObjectName("modify")
        self.verticalLayoutWidget = QtWidgets.QWidget(MscolabProject)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 70, 191, 441))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.collaboratorsList = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.collaboratorsList.setObjectName("collaboratorsList")
        self.verticalLayout_4.addWidget(self.collaboratorsList)
        self.delete_1 = QtWidgets.QPushButton(MscolabProject)
        self.delete_1.setGeometry(QtCore.QRect(350, 20, 51, 23))
        self.delete_1.setObjectName("delete_1")
        self.messageText = QtWidgets.QPlainTextEdit(MscolabProject)
        self.messageText.setGeometry(QtCore.QRect(220, 520, 281, 71))
        self.messageText.setObjectName("messageText")
        self.sendMessage = QtWidgets.QPushButton(MscolabProject)
        self.sendMessage.setGeometry(QtCore.QRect(540, 540, 80, 23))
        self.sendMessage.setObjectName("sendMessage")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(MscolabProject)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(220, 70, 391, 441))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.messages = QtWidgets.QListWidget(self.verticalLayoutWidget_3)
        self.messages.setObjectName("messages")
        self.verticalLayout_6.addWidget(self.messages)
        self.verticalLayoutWidget_4 = QtWidgets.QWidget(MscolabProject)
        self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(630, 70, 271, 521))
        self.verticalLayoutWidget_4.setObjectName("verticalLayoutWidget_4")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.changes = QtWidgets.QListWidget(self.verticalLayoutWidget_4)
        self.changes.setObjectName("changes")
        self.verticalLayout_7.addWidget(self.changes)

        self.retranslateUi(MscolabProject)
        QtCore.QMetaObject.connectSlotsByName(MscolabProject)

    def retranslateUi(self, MscolabProject):
        _translate = QtCore.QCoreApplication.translate
        MscolabProject.setWindowTitle(_translate("MscolabProject", "Mscolab Project"))
        self.accessLevel.setItemText(0, _translate("MscolabProject", "collaborator"))
        self.accessLevel.setItemText(1, _translate("MscolabProject", "admin"))
        self.accessLevel.setItemText(2, _translate("MscolabProject", "viewer"))
        self.add.setText(_translate("MscolabProject", "add"))
        self.modify.setText(_translate("MscolabProject", "modify"))
        self.delete_1.setText(_translate("MscolabProject", "delete"))
        self.messageText.setPlaceholderText(_translate("MscolabProject", "Enter message here"))
        self.sendMessage.setText(_translate("MscolabProject", "send"))

