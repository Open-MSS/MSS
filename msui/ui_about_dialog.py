# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_about_dialog.ui'
#
# Created by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_AboutMSUIDialog(object):
    def setupUi(self, AboutMSUIDialog):
        AboutMSUIDialog.setObjectName(_fromUtf8("AboutMSUIDialog"))
        AboutMSUIDialog.resize(529, 232)
        self.verticalLayout = QtGui.QVBoxLayout(AboutMSUIDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(AboutMSUIDialog)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 6, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(AboutMSUIDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.lblVersion = QtGui.QLabel(AboutMSUIDialog)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.verticalLayout.addWidget(self.lblVersion)
        spacerItem1 = QtGui.QSpacerItem(20, 7, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.label_3 = QtGui.QLabel(AboutMSUIDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout.addWidget(self.label_3)
        self.label_4 = QtGui.QLabel(AboutMSUIDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        spacerItem2 = QtGui.QSpacerItem(20, 6, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.label_5 = QtGui.QLabel(AboutMSUIDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.verticalLayout.addWidget(self.label_5)
        spacerItem3 = QtGui.QSpacerItem(20, 7, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.btOK = QtGui.QPushButton(AboutMSUIDialog)
        self.btOK.setObjectName(_fromUtf8("btOK"))
        self.horizontalLayout.addWidget(self.btOK)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(AboutMSUIDialog)
        QtCore.QObject.connect(self.btOK, QtCore.SIGNAL(_fromUtf8("clicked()")), AboutMSUIDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AboutMSUIDialog)

    def retranslateUi(self, AboutMSUIDialog):
        AboutMSUIDialog.setWindowTitle(_translate("AboutMSUIDialog", "About MSUI", None))
        self.label.setText(_translate("AboutMSUIDialog", "Mission Support System User Interface", None))
        self.label_2.setText(
            _translate("AboutMSUIDialog", "User Interface Application of the DLR/IPA Mission Support System", None))
        self.lblVersion.setText(_translate("AboutMSUIDialog", "--VERSION--", None))
        self.label_3.setText(
            _translate("AboutMSUIDialog", "Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.", None))
        self.label_4.setText(_translate("AboutMSUIDialog", "Copyright 2011-2014 Marc Rautenhaus", None))
        self.label_5.setText(_translate("AboutMSUIDialog", "See the files README, LICENSE, NOTICE for details.", None))
        self.btOK.setText(_translate("AboutMSUIDialog", "Ok", None))
