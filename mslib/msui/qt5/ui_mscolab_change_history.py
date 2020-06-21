# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_change_history.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ChangeHistory(object):
    def setupUi(self, ChangeHistory):
        ChangeHistory.setObjectName("ChangeHistory")
        ChangeHistory.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(ChangeHistory)
        self.centralwidget.setObjectName("centralwidget")
        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(150, 120, 508, 292))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.changes = QtWidgets.QListWidget(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.changes.sizePolicy().hasHeightForWidth())
        self.changes.setSizePolicy(sizePolicy)
        self.changes.setMinimumSize(QtCore.QSize(400, 280))
        self.changes.setObjectName("changes")
        self.horizontalLayout_6.addWidget(self.changes)
        self.checkout = QtWidgets.QPushButton(self.layoutWidget)
        self.checkout.setAutoDefault(False)
        self.checkout.setDefault(False)
        self.checkout.setObjectName("checkout")
        self.horizontalLayout_6.addWidget(self.checkout, 0, QtCore.Qt.AlignTop)
        ChangeHistory.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(ChangeHistory)
        self.statusbar.setObjectName("statusbar")
        ChangeHistory.setStatusBar(self.statusbar)

        self.retranslateUi(ChangeHistory)
        QtCore.QMetaObject.connectSlotsByName(ChangeHistory)

    def retranslateUi(self, ChangeHistory):
        _translate = QtCore.QCoreApplication.translate
        ChangeHistory.setWindowTitle(_translate("ChangeHistory", "Change history"))
        self.checkout.setText(_translate("ChangeHistory", "checkout"))

