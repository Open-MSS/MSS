# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_add_operation_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_addOperationDialog(object):
    def setupUi(self, addOperationDialog):
        addOperationDialog.setObjectName("addOperationDialog")
        addOperationDialog.resize(467, 303)
        self.buttonBox = QtWidgets.QDialogButtonBox(addOperationDialog)
        self.buttonBox.setGeometry(QtCore.QRect(280, 250, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(addOperationDialog)
        self.label.setGeometry(QtCore.QRect(70, 20, 30, 16))
        self.label.setObjectName("label")
        self.path = QtWidgets.QLineEdit(addOperationDialog)
        self.path.setGeometry(QtCore.QRect(110, 20, 341, 30))
        self.path.setObjectName("path")
        self.description = QtWidgets.QTextEdit(addOperationDialog)
        self.description.setGeometry(QtCore.QRect(110, 60, 341, 59))
        self.description.setObjectName("description")
        self.browse = QtWidgets.QPushButton(addOperationDialog)
        self.browse.setGeometry(QtCore.QRect(350, 210, 100, 30))
        self.browse.setObjectName("browse")
        self.label_3 = QtWidgets.QLabel(addOperationDialog)
        self.label_3.setGeometry(QtCore.QRect(20, 180, 201, 16))
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(addOperationDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 60, 80, 16))
        self.label_2.setObjectName("label_2")
        self.selectedFile = QtWidgets.QLineEdit(addOperationDialog)
        self.selectedFile.setEnabled(False)
        self.selectedFile.setGeometry(QtCore.QRect(20, 210, 320, 30))
        self.selectedFile.setReadOnly(True)
        self.selectedFile.setObjectName("selectedFile")
        self.label_4 = QtWidgets.QLabel(addOperationDialog)
        self.label_4.setGeometry(QtCore.QRect(40, 130, 60, 16))
        self.label_4.setObjectName("label_4")
        self.category = QtWidgets.QLineEdit(addOperationDialog)
        self.category.setGeometry(QtCore.QRect(110, 130, 341, 23))
        self.category.setObjectName("category")

        self.retranslateUi(addOperationDialog)
        self.buttonBox.accepted.connect(addOperationDialog.accept)
        self.buttonBox.rejected.connect(addOperationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addOperationDialog)

    def retranslateUi(self, addOperationDialog):
        _translate = QtCore.QCoreApplication.translate
        addOperationDialog.setWindowTitle(_translate("addOperationDialog", "Add operation"))
        self.label.setText(_translate("addOperationDialog", "Path:"))
        self.path.setPlaceholderText(_translate("addOperationDialog", "Operation Name (No spaces or special characters)"))
        self.description.setPlaceholderText(_translate("addOperationDialog", "Operation Descriptions"))
        self.browse.setText(_translate("addOperationDialog", "browse..."))
        self.label_3.setText(_translate("addOperationDialog", "Choose Flighttrack File (Optional):"))
        self.label_2.setText(_translate("addOperationDialog", "Description:"))
        self.selectedFile.setPlaceholderText(_translate("addOperationDialog", "(use browse to pick a file)"))
        self.label_4.setText(_translate("addOperationDialog", "Category:"))
        self.category.setText(_translate("addOperationDialog", "default"))
        self.category.setPlaceholderText(_translate("addOperationDialog", "Category (ANY)"))
