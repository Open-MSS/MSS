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
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.jsonWidget = QtWidgets.QWidget(self.centralwidget)
        self.jsonWidget.setObjectName("jsonWidget")
        self.gridLayout_2.addWidget(self.jsonWidget, 1, 0, 1, 1)
        self.expandCollapseLabel = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.expandCollapseLabel.setFont(font)
        self.expandCollapseLabel.setObjectName("expandCollapseLabel")
        self.gridLayout_2.addWidget(self.expandCollapseLabel, 0, 0, 1, 1, QtCore.Qt.AlignRight|QtCore.Qt.AlignBottom)
        self.gridLayout_2.setRowStretch(1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.centralwidget)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Open|QtWidgets.QDialogButtonBox.RestoreDefaults|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.gridLayout.setRowStretch(1, 1)
        ConfigurationEditorWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ConfigurationEditorWindow)
        self.statusbar.setObjectName("statusbar")
        ConfigurationEditorWindow.setStatusBar(self.statusbar)

        self.retranslateUi(ConfigurationEditorWindow)
        QtCore.QMetaObject.connectSlotsByName(ConfigurationEditorWindow)

    def retranslateUi(self, ConfigurationEditorWindow):
        _translate = QtCore.QCoreApplication.translate
        ConfigurationEditorWindow.setWindowTitle(_translate("ConfigurationEditorWindow", "MSS Configuration Editor"))
        self.optTitleLabel.setText(_translate("ConfigurationEditorWindow", "Configuration Options:"))
        self.addOptBtn.setText(_translate("ConfigurationEditorWindow", "+ Add"))
        self.removeOptBtn.setText(_translate("ConfigurationEditorWindow", "- Remove"))
        self.expandCollapseLabel.setText(_translate("ConfigurationEditorWindow", "Expand All"))
