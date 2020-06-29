# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_version_history.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MscolabVersionHistory(object):
    def setupUi(self, MscolabVersionHistory):
        MscolabVersionHistory.setObjectName("MscolabVersionHistory")
        MscolabVersionHistory.resize(707, 463)
        self.centralwidget = QtWidgets.QWidget(MscolabVersionHistory)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.usernameLabel = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.usernameLabel.sizePolicy().hasHeightForWidth())
        self.usernameLabel.setSizePolicy(sizePolicy)
        self.usernameLabel.setObjectName("usernameLabel")
        self.horizontalLayout_3.addWidget(self.usernameLabel)
        self.projectNameLabel = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.projectNameLabel.sizePolicy().hasHeightForWidth())
        self.projectNameLabel.setSizePolicy(sizePolicy)
        self.projectNameLabel.setObjectName("projectNameLabel")
        self.horizontalLayout_3.addWidget(self.projectNameLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 1)
        self.horizontalLayout_3.setStretch(2, 2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.changes = QtWidgets.QListWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.changes.sizePolicy().hasHeightForWidth())
        self.changes.setSizePolicy(sizePolicy)
        self.changes.setMinimumSize(QtCore.QSize(400, 280))
        self.changes.setObjectName("changes")
        self.horizontalLayout_6.addWidget(self.changes)
        self.checkout = QtWidgets.QPushButton(self.centralwidget)
        self.checkout.setAutoDefault(False)
        self.checkout.setDefault(False)
        self.checkout.setObjectName("checkout")
        self.horizontalLayout_6.addWidget(self.checkout, 0, QtCore.Qt.AlignTop)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        MscolabVersionHistory.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MscolabVersionHistory)
        self.statusbar.setObjectName("statusbar")
        MscolabVersionHistory.setStatusBar(self.statusbar)

        self.retranslateUi(MscolabVersionHistory)
        QtCore.QMetaObject.connectSlotsByName(MscolabVersionHistory)

    def retranslateUi(self, MscolabVersionHistory):
        _translate = QtCore.QCoreApplication.translate
        MscolabVersionHistory.setWindowTitle(_translate("MscolabVersionHistory", "Version History"))
        self.usernameLabel.setText(_translate("MscolabVersionHistory", "Logged In: "))
        self.projectNameLabel.setText(_translate("MscolabVersionHistory", "Project:"))
        self.checkout.setText(_translate("MscolabVersionHistory", "checkout"))

