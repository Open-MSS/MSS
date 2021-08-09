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
        self.moveUpTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveUpTb.setObjectName("moveUpTb")
        self.horizontalLayout_4.addWidget(self.moveUpTb)
        self.moveDownTb = QtWidgets.QToolButton(self.centralwidget)
        self.moveDownTb.setObjectName("moveDownTb")
        self.horizontalLayout_4.addWidget(self.moveDownTb)
        self.horizontalLayout_4.setStretch(0, 1)
        self.horizontalLayout_4.setStretch(1, 1)
        self.horizontalLayout_4.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.jsonWidget = QtWidgets.QWidget(self.centralwidget)
        self.jsonWidget.setObjectName("jsonWidget")
        self.verticalLayout.addWidget(self.jsonWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.restoreDefaultsBtn = QtWidgets.QPushButton(self.centralwidget)
        self.restoreDefaultsBtn.setObjectName("restoreDefaultsBtn")
        self.horizontalLayout.addWidget(self.restoreDefaultsBtn)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.importBtn = QtWidgets.QPushButton(self.centralwidget)
        self.importBtn.setObjectName("importBtn")
        self.horizontalLayout.addWidget(self.importBtn)
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout.addWidget(self.line_2)
        self.cancelBtn = QtWidgets.QPushButton(self.centralwidget)
        self.cancelBtn.setObjectName("cancelBtn")
        self.horizontalLayout.addWidget(self.cancelBtn)
        self.saveAsBtn = QtWidgets.QPushButton(self.centralwidget)
        self.saveAsBtn.setObjectName("saveAsBtn")
        self.horizontalLayout.addWidget(self.saveAsBtn)
        self.saveBtn = QtWidgets.QPushButton(self.centralwidget)
        self.saveBtn.setObjectName("saveBtn")
        self.horizontalLayout.addWidget(self.saveBtn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(1, 1)
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
        self.restoreDefaultsBtn.setText(_translate("ConfigurationEditorWindow", "Restore Defaults"))
        self.importBtn.setText(_translate("ConfigurationEditorWindow", "Import"))
        self.cancelBtn.setText(_translate("ConfigurationEditorWindow", "Cancel"))
        self.saveAsBtn.setText(_translate("ConfigurationEditorWindow", "Save As"))
        self.saveBtn.setText(_translate("ConfigurationEditorWindow", "Save"))
