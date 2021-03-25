# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_add_project.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_addProjectDialog(object):
    def setupUi(self, addProjectDialog):
        addProjectDialog.setObjectName("addProjectDialog")
        addProjectDialog.resize(467, 256)
        self.buttonBox = QtWidgets.QDialogButtonBox(addProjectDialog)
        self.buttonBox.setGeometry(QtCore.QRect(280, 210, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(addProjectDialog)
        self.label.setGeometry(QtCore.QRect(70, 20, 30, 16))
        self.label.setObjectName("label")
        self.path = QtWidgets.QLineEdit(addProjectDialog)
        self.path.setGeometry(QtCore.QRect(110, 20, 341, 30))
        self.path.setObjectName("path")
        self.description = QtWidgets.QTextEdit(addProjectDialog)
        self.description.setGeometry(QtCore.QRect(110, 60, 341, 59))
        self.description.setObjectName("description")
        self.browse = QtWidgets.QPushButton(addProjectDialog)
        self.browse.setGeometry(QtCore.QRect(350, 150, 100, 30))
        self.browse.setObjectName("browse")
        self.label_3 = QtWidgets.QLabel(addProjectDialog)
        self.label_3.setGeometry(QtCore.QRect(20, 134, 201, 16))
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(addProjectDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 60, 80, 16))
        self.label_2.setObjectName("label_2")
        self.selectedFile = QtWidgets.QLineEdit(addProjectDialog)
        self.selectedFile.setEnabled(False)
        self.selectedFile.setGeometry(QtCore.QRect(20, 150, 320, 30))
        self.selectedFile.setReadOnly(True)
        self.selectedFile.setObjectName("selectedFile")

        self.retranslateUi(addProjectDialog)
        self.buttonBox.accepted.connect(addProjectDialog.accept)
        self.buttonBox.rejected.connect(addProjectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addProjectDialog)

    def retranslateUi(self, addProjectDialog):
        _translate = QtCore.QCoreApplication.translate
        addProjectDialog.setWindowTitle(_translate("addProjectDialog", "Add project"))
        self.label.setText(_translate("addProjectDialog", "Path:"))
        self.path.setPlaceholderText(_translate("addProjectDialog", "Project Name (No spaces or special characters)"))
        self.description.setPlaceholderText(_translate("addProjectDialog", "Project Descriptions"))
        self.browse.setText(_translate("addProjectDialog", "browse..."))
        self.label_3.setText(_translate("addProjectDialog", "Choose FTML File (Optional)"))
        self.label_2.setText(_translate("addProjectDialog", "Description"))
        self.selectedFile.setPlaceholderText(_translate("addProjectDialog", "(use browse to pick a file)"))
