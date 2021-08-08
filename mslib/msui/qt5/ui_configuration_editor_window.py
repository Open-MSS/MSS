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
        ConfigurationEditorWindow.resize(593, 656)
        self.centralwidget = QtWidgets.QWidget(ConfigurationEditorWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(8, 8, 8, 8)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.optCb = QtWidgets.QComboBox(self.centralwidget)
        self.optCb.setObjectName("optCb")
        self.horizontalLayout_4.addWidget(self.optCb)
        self.addOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.addOptBtn.setObjectName("addOptBtn")
        self.horizontalLayout_4.addWidget(self.addOptBtn)
        self.removeOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.removeOptBtn.setObjectName("removeOptBtn")
        self.horizontalLayout_4.addWidget(self.removeOptBtn)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
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
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.jsonWidget = QtWidgets.QWidget(self.centralwidget)
        self.jsonWidget.setObjectName("jsonWidget")
        self.verticalLayout.addWidget(self.jsonWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.centralwidget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Open|QtWidgets.QDialogButtonBox.RestoreDefaults|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout.setStretch(2, 1)
        ConfigurationEditorWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ConfigurationEditorWindow)
        self.statusbar.setObjectName("statusbar")
        ConfigurationEditorWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ConfigurationEditorWindow)
        QtCore.QMetaObject.connectSlotsByName(ConfigurationEditorWindow)

    def retranslateUi(self, ConfigurationEditorWindow):
        _translate = QtCore.QCoreApplication.translate
        ConfigurationEditorWindow.setWindowTitle(_translate("ConfigurationEditorWindow", "MSS Configuration Editor"))
        self.addOptBtn.setText(_translate("ConfigurationEditorWindow", "+ Add"))
        self.removeOptBtn.setText(_translate("ConfigurationEditorWindow", "- Remove"))
        self.moveUpTb.setText(_translate("ConfigurationEditorWindow", "..."))
        self.moveDownTb.setText(_translate("ConfigurationEditorWindow", "..."))
