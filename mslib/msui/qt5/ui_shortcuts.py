# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_shortcuts.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!
# -*- coding: utf-8 -*-
#
# This Python file was auto-generated from a .ui file using the PyQt5 UI code generator 5.12.3.
# Manual modifications to this file may be lost if it is re-generated.
#
# To modify the UI, edit the original .ui file and regenerate this Python file.



from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ShortcutsDialog(object):
    def setupUi(self, ShortcutsDialog):
        ShortcutsDialog.setObjectName("ShortcutsDialog")
        ShortcutsDialog.resize(478, 371)
        self.verticalLayout = QtWidgets.QVBoxLayout(ShortcutsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(ShortcutsDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.leShortcutFilter = QtWidgets.QLineEdit(ShortcutsDialog)
        self.leShortcutFilter.setObjectName("leShortcutFilter")
        self.horizontalLayout.addWidget(self.leShortcutFilter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.cbNoShortcut = QtWidgets.QCheckBox(ShortcutsDialog)
        self.cbNoShortcut.setObjectName("cbNoShortcut")
        self.horizontalLayout_3.addWidget(self.cbNoShortcut)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.line = QtWidgets.QFrame(ShortcutsDialog)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout_3.addWidget(self.line)
        self.label_2 = QtWidgets.QLabel(ShortcutsDialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.cbDisplayType = QtWidgets.QComboBox(ShortcutsDialog)
        self.cbDisplayType.setObjectName("cbDisplayType")
        self.cbDisplayType.addItem("")
        self.cbDisplayType.addItem("")
        self.cbDisplayType.addItem("")
        self.horizontalLayout_3.addWidget(self.cbDisplayType)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.treeWidget = QtWidgets.QTreeWidget(ShortcutsDialog)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.treeWidget.header().setCascadingSectionResizes(True)
        self.verticalLayout.addWidget(self.treeWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.cbAdvanced = QtWidgets.QCheckBox(ShortcutsDialog)
        self.cbAdvanced.setObjectName("cbAdvanced")
        self.horizontalLayout_2.addWidget(self.cbAdvanced)
        self.cbHighlight = QtWidgets.QCheckBox(ShortcutsDialog)
        self.cbHighlight.setObjectName("cbHighlight")
        self.horizontalLayout_2.addWidget(self.cbHighlight)
        self.buttonBox = QtWidgets.QDialogButtonBox(ShortcutsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(ShortcutsDialog)
        self.buttonBox.accepted.connect(ShortcutsDialog.accept)
        self.buttonBox.rejected.connect(ShortcutsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ShortcutsDialog)
        # Add this if possible as this will enhance the shortcut feature implementation
        # self.filterLabel = QtWidgets.QLabel(ShortcutsDialog)
        # self.filterLabel.setObjectName("filterLabel")
        # self.shortcutFilterInput = QtWidgets.QLineEdit(ShortcutsDialog)
        # self.shortcutFilterInput.setObjectName("shortcutFilterInput")
        # self.shortcutTreeWidget = QtWidgets.QTreeWidget(ShortcutsDialog)
        # self.shortcutTreeWidget.setObjectName("shortcutTreeWidget")


    def retranslateUi(self, ShortcutsDialog):
        _translate = QtCore.QCoreApplication.translate
        ShortcutsDialog.setWindowTitle(_translate("ShortcutsDialog", "Shortcuts"))
        self.label.setText(_translate("ShortcutsDialog", "Filter:"))
        self.cbNoShortcut.setText(_translate("ShortcutsDialog", "Show items without shortcut"))
        self.label_2.setText(_translate("ShortcutsDialog", "Display type:"))
        self.cbDisplayType.setItemText(0, _translate("ShortcutsDialog", "Tooltip"))
        self.cbDisplayType.setItemText(1, _translate("ShortcutsDialog", "Text"))
        self.cbDisplayType.setItemText(2, _translate("ShortcutsDialog", "ObjectName"))
        self.cbAdvanced.setText(_translate("ShortcutsDialog", "Advanced Settings"))
        self.cbHighlight.setText(_translate("ShortcutsDialog", "Highlight on all Windows"))
        self.filterLabel.setToolTip("Type here to filter the shortcuts")
self.cbNoShortcut.setAccessibleDescription("Show or hide items without shortcuts")

