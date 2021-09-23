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
        ConfigurationEditorWindow.resize(639, 676)
        self.centralwidget = QtWidgets.QWidget(ConfigurationEditorWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.optCb = QtWidgets.QComboBox(self.centralwidget)
        self.optCb.setObjectName("optCb")
        self.horizontalLayout_4.addWidget(self.optCb)
        self.addOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.addOptBtn.setObjectName("addOptBtn")
        self.horizontalLayout_4.addWidget(self.addOptBtn)
        self.removeOptBtn = QtWidgets.QPushButton(self.centralwidget)
        self.removeOptBtn.setObjectName("removeOptBtn")
        self.horizontalLayout_4.addWidget(self.removeOptBtn)
        self.restoreDefaultsBtn = QtWidgets.QPushButton(self.centralwidget)
        self.restoreDefaultsBtn.setObjectName("restoreDefaultsBtn")
        self.horizontalLayout_4.addWidget(self.restoreDefaultsBtn)
        self.moveUpTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveUpTb.setObjectName("moveUpTb")
        self.horizontalLayout_4.addWidget(self.moveUpTb)
        self.moveDownTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveDownTb.setObjectName("moveDownTb")
        self.horizontalLayout_4.addWidget(self.moveDownTb)
        self.horizontalLayout_4.setStretch(1, 1)
        self.horizontalLayout_4.setStretch(2, 1)
        self.horizontalLayout_4.setStretch(3, 1)
        self.horizontalLayout_4.setStretch(4, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.jsonWidget = QtWidgets.QWidget(self.centralwidget)
        self.jsonWidget.setObjectName("jsonWidget")
        self.verticalLayout.addWidget(self.jsonWidget)
        self.verticalLayout.setStretch(1, 1)
        self.actionCloseWindow = QtWidgets.QAction(ConfigurationEditorWindow)
        self.actionCloseWindow.setObjectName("actionCloseWindow")
        ConfigurationEditorWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ConfigurationEditorWindow)
        self.statusbar.setObjectName("statusbar")
        ConfigurationEditorWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(ConfigurationEditorWindow)
        self.toolBar.setObjectName("toolBar")
        ConfigurationEditorWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.centralwidget.addAction(self.actionCloseWindow)

        self.retranslateUi(ConfigurationEditorWindow)
        self.actionCloseWindow.triggered.connect(ConfigurationEditorWindow.close)
        QtCore.QMetaObject.connectSlotsByName(ConfigurationEditorWindow)

    def retranslateUi(self, ConfigurationEditorWindow):
        _translate = QtCore.QCoreApplication.translate
        ConfigurationEditorWindow.setWindowTitle(_translate("ConfigurationEditorWindow", "MSS Configuration Editor"))
        self.label.setText(_translate("ConfigurationEditorWindow", "Filter :"))
        self.optCb.setToolTip(_translate("ConfigurationEditorWindow", "Select option to filter the view"))
        self.addOptBtn.setToolTip(_translate("ConfigurationEditorWindow", "Select an option to add new value"))
        self.addOptBtn.setText(_translate("ConfigurationEditorWindow", "+ Add"))
        self.removeOptBtn.setToolTip(_translate("ConfigurationEditorWindow", "Select one/more options to remove"))
        self.removeOptBtn.setText(_translate("ConfigurationEditorWindow", "- Remove"))
        self.restoreDefaultsBtn.setToolTip(_translate("ConfigurationEditorWindow", "Select one/more options to restore default value"))
        self.restoreDefaultsBtn.setText(_translate("ConfigurationEditorWindow", "Restore Defaults"))
        self.moveUpTb.setText(_translate("ConfigurationEditorWindow", "..."))
        self.moveDownTb.setText(_translate("ConfigurationEditorWindow", "..."))
        self.actionCloseWindow.setText(_translate("ConfigurationEditorWindow", "CloseWindow"))
        self.actionCloseWindow.setShortcut(_translate("ConfigurationEditorWindow", "Ctrl+W"))
        self.toolBar.setWindowTitle(_translate("ConfigurationEditorWindow", "toolBar"))
