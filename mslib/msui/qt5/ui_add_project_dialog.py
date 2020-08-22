# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_add_project.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_addProjectDialog(object):
    def setupUi(self, addProjectDialog):
        addProjectDialog.setObjectName("addProjectDialog")
        addProjectDialog.resize(467, 226)
        self.buttonBox = QtWidgets.QDialogButtonBox(addProjectDialog)
        self.buttonBox.setGeometry(QtCore.QRect(260, 190, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(addProjectDialog)
        self.label.setGeometry(QtCore.QRect(80, 30, 32, 16))
        self.label.setObjectName("label")
        self.path = QtWidgets.QLineEdit(addProjectDialog)
        self.path.setGeometry(QtCore.QRect(120, 20, 301, 31))
        self.path.setObjectName("path")
        self.description = QtWidgets.QTextEdit(addProjectDialog)
        self.description.setGeometry(QtCore.QRect(120, 60, 301, 59))
        self.description.setObjectName("description")
        self.browse = QtWidgets.QPushButton(addProjectDialog)
        self.browse.setGeometry(QtCore.QRect(270, 130, 98, 32))
        self.browse.setObjectName("browse")
        self.selectedFile = QtWidgets.QLabel(addProjectDialog)
        self.selectedFile.setGeometry(QtCore.QRect(190, 90, 59, 21))
        self.selectedFile.setText("")
        self.selectedFile.setObjectName("selectedFile")
        self.label_3 = QtWidgets.QLabel(addProjectDialog)
        self.label_3.setGeometry(QtCore.QRect(41, 134, 181, 16))
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(addProjectDialog)
        self.label_2.setGeometry(QtCore.QRect(40, 60, 74, 16))
        self.label_2.setObjectName("label_2")

        self.retranslateUi(addProjectDialog)
        self.buttonBox.accepted.connect(addProjectDialog.accept)
        self.buttonBox.rejected.connect(addProjectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addProjectDialog)

    def retranslateUi(self, addProjectDialog):
        _translate = QtCore.QCoreApplication.translate
        addProjectDialog.setWindowTitle(_translate("addProjectDialog", "Add project"))
        self.label.setText(_translate("addProjectDialog", "Path:"))
        self.path.setPlaceholderText(_translate("addProjectDialog", "Project Name(No spaces or special characters)"))
        self.description.setPlaceholderText(_translate("addProjectDialog", "Project Descriptions"))
        self.browse.setText(_translate("addProjectDialog", "browse..."))
        self.label_3.setText(_translate("addProjectDialog", "Choose FTML File (Optional)"))
        self.label_2.setText(_translate("addProjectDialog", "Description:"))

