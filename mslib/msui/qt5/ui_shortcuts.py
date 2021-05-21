# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_shortcuts.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ShortcutsDialog(object):
    def setupUi(self, ShortcutsDialog):
        ShortcutsDialog.setObjectName("ShortcutsDialog")
        ShortcutsDialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(ShortcutsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeWidget = QtWidgets.QTreeWidget(ShortcutsDialog)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.treeWidget.header().setCascadingSectionResizes(True)
        self.verticalLayout.addWidget(self.treeWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(ShortcutsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ShortcutsDialog)
        self.buttonBox.accepted.connect(ShortcutsDialog.accept)
        self.buttonBox.rejected.connect(ShortcutsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ShortcutsDialog)

    def retranslateUi(self, ShortcutsDialog):
        _translate = QtCore.QCoreApplication.translate
        ShortcutsDialog.setWindowTitle(_translate("ShortcutsDialog", "Shortcuts"))
