# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_multiple_flightpath_dockwidget.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MultipleViewWidget(object):
    def setupUi(self, MultipleViewWidget):
        MultipleViewWidget.setObjectName("MultipleViewWidget")
        MultipleViewWidget.resize(544, 235)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MultipleViewWidget.sizePolicy().hasHeightForWidth())
        MultipleViewWidget.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(MultipleViewWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.list_flighttrack = QtWidgets.QListWidget(MultipleViewWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.list_flighttrack.sizePolicy().hasHeightForWidth())
        self.list_flighttrack.setSizePolicy(sizePolicy)
        self.list_flighttrack.setObjectName("list_flighttrack")
        self.horizontalLayout_2.addWidget(self.list_flighttrack)
        self.horizontalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.labelStatus = QtWidgets.QLabel(MultipleViewWidget)
        self.labelStatus.setObjectName("labelStatus")
        self.verticalLayout_2.addWidget(self.labelStatus)

        self.retranslateUi(MultipleViewWidget)
        QtCore.QMetaObject.connectSlotsByName(MultipleViewWidget)

    def retranslateUi(self, MultipleViewWidget):
        _translate = QtCore.QCoreApplication.translate
        MultipleViewWidget.setWindowTitle(_translate("MultipleViewWidget", "Form"))
        self.labelStatus.setText(_translate("MultipleViewWidget", "Status: "))
