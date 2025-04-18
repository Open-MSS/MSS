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
        addOperationDialog.resize(460, 351)
        self.buttonBox = QtWidgets.QDialogButtonBox(addOperationDialog)
        self.buttonBox.setGeometry(QtCore.QRect(280, 310, 171, 32))
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
        self.label_2 = QtWidgets.QLabel(addOperationDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 60, 80, 16))
        self.label_2.setObjectName("label_2")
        self.label_4 = QtWidgets.QLabel(addOperationDialog)
        self.label_4.setGeometry(QtCore.QRect(40, 130, 60, 16))
        self.label_4.setObjectName("label_4")
        self.category = QtWidgets.QLineEdit(addOperationDialog)
        self.category.setGeometry(QtCore.QRect(110, 130, 341, 23))
        self.category.setObjectName("category")
        self.optFileBox = QtWidgets.QGroupBox(addOperationDialog)
        self.optFileBox.setGeometry(QtCore.QRect(30, 180, 421, 121))
        self.optFileBox.setObjectName("optFileBox")
        self.label_3 = QtWidgets.QLabel(self.optFileBox)
        self.label_3.setGeometry(QtCore.QRect(0, 20, 59, 15))
        self.label_3.setObjectName("label_3")
        self.cb_ImportType = QtWidgets.QComboBox(self.optFileBox)
        self.cb_ImportType.setGeometry(QtCore.QRect(60, 20, 79, 23))
        self.cb_ImportType.setCurrentText("")
        self.cb_ImportType.setObjectName("cb_ImportType")
        self.selectedFile = QtWidgets.QLineEdit(self.optFileBox)
        self.selectedFile.setEnabled(False)
        self.selectedFile.setGeometry(QtCore.QRect(0, 80, 311, 30))
        self.selectedFile.setReadOnly(True)
        self.selectedFile.setObjectName("selectedFile")
        self.browse = QtWidgets.QPushButton(self.optFileBox)
        self.browse.setGeometry(QtCore.QRect(320, 80, 100, 30))
        self.browse.setObjectName("browse")

        self.retranslateUi(addOperationDialog)
        self.cb_ImportType.setCurrentIndex(-1)
        self.buttonBox.accepted.connect(addOperationDialog.accept)
        self.buttonBox.rejected.connect(addOperationDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addOperationDialog)

    def retranslateUi(self, addOperationDialog):
        _translate = QtCore.QCoreApplication.translate
        addOperationDialog.setWindowTitle(_translate("addOperationDialog", "Add operation"))
        self.label.setText(_translate("addOperationDialog", "Path:"))
        self.path.setToolTip(_translate("addOperationDialog", "<html><head/><body><p>add the name of your Operation</p></body></html>"))
        self.path.setPlaceholderText(_translate("addOperationDialog", "Operation Name (No spaces or special characters)"))
        self.description.setToolTip(_translate("addOperationDialog", "<html><head/><body><p>Add a description of your Operation</p></body></html>"))
        self.description.setPlaceholderText(_translate("addOperationDialog", "Operation Descriptions"))
        self.label_2.setText(_translate("addOperationDialog", "Description:"))
        self.label_4.setText(_translate("addOperationDialog", "Category:"))
        self.category.setToolTip(_translate("addOperationDialog", "<html><head/><body><p>Set a Category to filter your Operations</p></body></html>"))
        self.category.setText(_translate("addOperationDialog", "default"))
        self.category.setPlaceholderText(_translate("addOperationDialog", "Category (ANY)"))
        self.optFileBox.setTitle(_translate("addOperationDialog", "Choose Flight Track File (Optional)"))
        self.label_3.setText(_translate("addOperationDialog", "Type:"))
        self.cb_ImportType.setToolTip(_translate("addOperationDialog", "<html><head/><body><p>Select Import Type</p></body></html>"))
        self.selectedFile.setPlaceholderText(_translate("addOperationDialog", "(use browse to pick a file)"))
        self.browse.setText(_translate("addOperationDialog", "browse..."))
