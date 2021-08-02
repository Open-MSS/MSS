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
        ConfigurationEditorWindow.resize(647, 656)
        self.centralwidget = QtWidgets.QWidget(ConfigurationEditorWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.jsonWidget = QtWidgets.QWidget(self.centralwidget)
        self.jsonWidget.setObjectName("jsonWidget")
        self.gridLayout.addWidget(self.jsonWidget, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.moveUpTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveUpTb.setObjectName("moveUpTb")
        self.horizontalLayout.addWidget(self.moveUpTb)
        self.moveDownTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveDownTb.setObjectName("moveDownTb")
        self.horizontalLayout.addWidget(self.moveDownTb)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.centralwidget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Open|QtWidgets.QDialogButtonBox.RestoreDefaults|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.optTitleLabel = QtWidgets.QLabel(self.centralwidget)
        self.optTitleLabel.setObjectName("optTitleLabel")
        self.horizontalLayout_4.addWidget(self.optTitleLabel)
        self.optCb = QtWidgets.QComboBox(self.centralwidget)
        self.optCb.setObjectName("optCb")
        self.horizontalLayout_4.addWidget(self.optCb)
        self.addOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.addOptBtn.setObjectName("addOptBtn")
        self.horizontalLayout_4.addWidget(self.addOptBtn)
        self.removeOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.removeOptBtn.setObjectName("removeOptBtn")
        self.horizontalLayout_4.addWidget(self.removeOptBtn)
        self.horizontalLayout_4.setStretch(1, 1)
        self.horizontalLayout_4.setStretch(2, 1)
        self.horizontalLayout_4.setStretch(3, 1)
        self.gridLayout.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)
        self.gridLayout.setRowStretch(2, 1)
        ConfigurationEditorWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ConfigurationEditorWindow)
        self.statusbar.setObjectName("statusbar")
        ConfigurationEditorWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ConfigurationEditorWindow)
        QtCore.QMetaObject.connectSlotsByName(ConfigurationEditorWindow)

    def retranslateUi(self, ConfigurationEditorWindow):
        _translate = QtCore.QCoreApplication.translate
        ConfigurationEditorWindow.setWindowTitle(_translate("ConfigurationEditorWindow", "MSS Configuration Editor"))
        self.moveUpTb.setText(_translate("ConfigurationEditorWindow", "..."))
        self.moveDownTb.setText(_translate("ConfigurationEditorWindow", "..."))
        self.optTitleLabel.setText(_translate("ConfigurationEditorWindow", "Configuration Options:"))
        self.addOptBtn.setText(_translate("ConfigurationEditorWindow", "+ Add"))
        self.removeOptBtn.setText(_translate("ConfigurationEditorWindow", "- Remove"))
