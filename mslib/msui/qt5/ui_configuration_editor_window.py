# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_configuration_editor_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ConfigurationEditorWindow(object):
    def setupUi(self, ConfigurationEditorWindow):
        ConfigurationEditorWindow.setObjectName("ConfigurationEditorWindow")
        ConfigurationEditorWindow.resize(800, 524)
        self.centralwidget = QtWidgets.QWidget(ConfigurationEditorWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.frame)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.gridLayout_4.addWidget(self.frame, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setObjectName("comboBox")
        self.gridLayout_4.addWidget(self.comboBox, 1, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_4.addWidget(self.pushButton, 1, 2, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_4.addWidget(self.pushButton_2, 2, 0, 1, 1, QtCore.Qt.AlignLeft)
        self.gridLayout_4.setColumnStretch(0, 1)
        self.gridLayout_4.setColumnStretch(1, 1)
        self.gridLayout_4.setColumnStretch(2, 1)
        self.gridLayout.addLayout(self.gridLayout_4, 0, 0, 1, 1)
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setObjectName("widget")
        self.gridLayout.addWidget(self.widget, 1, 0, 1, 1)
        self.gridLayout.setRowStretch(1, 1)
        ConfigurationEditorWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ConfigurationEditorWindow)
        self.statusbar.setObjectName("statusbar")
        ConfigurationEditorWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ConfigurationEditorWindow)
        QtCore.QMetaObject.connectSlotsByName(ConfigurationEditorWindow)

    def retranslateUi(self, ConfigurationEditorWindow):
        _translate = QtCore.QCoreApplication.translate
        ConfigurationEditorWindow.setWindowTitle(_translate("ConfigurationEditorWindow", "ConfigurationEditorWindow"))
        self.label.setText(_translate("ConfigurationEditorWindow", "Configuration Options:"))
        self.pushButton.setText(_translate("ConfigurationEditorWindow", "Add to settings"))
        self.pushButton_2.setText(_translate("ConfigurationEditorWindow", "Show all"))
