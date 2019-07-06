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
        self.groupBox = QtWidgets.QGroupBox(MSSMscolabWindow)
        self.groupBox.setGeometry(QtCore.QRect(30, 70, 406, 163))
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listProjects = QtWidgets.QListWidget(self.groupBox)
        self.listProjects.setAlternatingRowColors(False)
        self.listProjects.setTextElideMode(QtCore.Qt.ElideNone)
        self.listProjects.setObjectName("listProjects")
        self.verticalLayout.addWidget(self.listProjects)
        self.widget = QtWidgets.QWidget(MSSMscolabWindow)
        self.widget.setGeometry(QtCore.QRect(30, 20, 401, 41))
        self.widget.setObjectName("widget")
        self.emailid = QtWidgets.QLineEdit(self.widget)
        self.emailid.setGeometry(QtCore.QRect(0, 10, 113, 23))
        self.emailid.setObjectName("emailid")
        self.password = QtWidgets.QLineEdit(self.widget)
        self.password.setGeometry(QtCore.QRect(130, 10, 113, 23))
        self.password.setObjectName("password")
        self.loginButton = QtWidgets.QPushButton(self.widget)
        self.loginButton.setGeometry(QtCore.QRect(270, 10, 80, 23))
        self.loginButton.setObjectName("loginButton")
        self.widget_2 = QtWidgets.QWidget(MSSMscolabWindow)
        self.widget_2.setEnabled(True)
        self.widget_2.setGeometry(QtCore.QRect(30, 10, 401, 41))
        self.widget_2.setObjectName("widget_2")
        self.label = QtWidgets.QLabel(self.widget_2)
        self.label.setGeometry(QtCore.QRect(50, 10, 251, 16))
        self.label.setObjectName("label")
        self.logoutButton = QtWidgets.QPushButton(self.widget_2)
        self.logoutButton.setGeometry(QtCore.QRect(280, 10, 80, 23))
        self.logoutButton.setObjectName("logoutButton")

        self.retranslateUi(MSSMscolabWindow)
        QtCore.QMetaObject.connectSlotsByName(MSSMscolabWindow)

    def retranslateUi(self, MSSMscolabWindow):
        _translate = QtCore.QCoreApplication.translate
        MSSMscolabWindow.setWindowTitle(_translate("MSSMscolabWindow", "Form"))
        self.groupBox.setTitle(_translate("MSSMscolabWindow", "Project listing"))
        self.listProjects.setToolTip(_translate("MSSMscolabWindow", "List of mscolab projects."))
        self.emailid.setPlaceholderText(_translate("MSSMscolabWindow", "emailid"))
        self.password.setPlaceholderText(_translate("MSSMscolabWindow", "password"))
        self.loginButton.setText(_translate("MSSMscolabWindow", "login"))
        self.label.setText(_translate("MSSMscolabWindow", "TextLabel"))
        self.logoutButton.setText(_translate("MSSMscolabWindow", "logout"))

