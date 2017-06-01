# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_imageloop_load_dialog.ui'
#
# Created: Wed Sep  8 11:40:36 2010
#      by: PyQt4 UI code generator 4.6.1
#
# WARNING! All changes made in this file will be lost!


from PyQt4 import QtCore, QtGui


class Ui_ProductChooserDialog(object):
    def setupUi(self, ProductChooserDialog):
        ProductChooserDialog.setObjectName("ProductChooserDialog")
        ProductChooserDialog.resize(372, 187)
        self.verticalLayout = QtGui.QVBoxLayout(ProductChooserDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_5 = QtGui.QLabel(ProductChooserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setMinimumSize(QtCore.QSize(50, 0))
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.cbType = QtGui.QComboBox(ProductChooserDialog)
        self.cbType.setObjectName("cbType")
        self.cbType.addItem("")
        self.horizontalLayout.addWidget(self.cbType)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_4 = QtGui.QLabel(ProductChooserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setMinimumSize(QtCore.QSize(50, 0))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.cbProduct = QtGui.QComboBox(ProductChooserDialog)
        self.cbProduct.setObjectName("cbProduct")
        self.cbProduct.addItem("")
        self.horizontalLayout_2.addWidget(self.cbProduct)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_6 = QtGui.QLabel(ProductChooserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setMinimumSize(QtCore.QSize(50, 0))
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_3.addWidget(self.label_6)
        self.cbRegion = QtGui.QComboBox(ProductChooserDialog)
        self.cbRegion.setObjectName("cbRegion")
        self.cbRegion.addItem("")
        self.horizontalLayout_3.addWidget(self.cbRegion)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_2 = QtGui.QLabel(ProductChooserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QtCore.QSize(80, 0))
        self.label_2.setMaximumSize(QtCore.QSize(80, 16777215))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_4.addWidget(self.label_2)
        self.tbInitTime_back = QtGui.QToolButton(ProductChooserDialog)
        self.tbInitTime_back.setArrowType(QtCore.Qt.LeftArrow)
        self.tbInitTime_back.setObjectName("tbInitTime_back")
        self.horizontalLayout_4.addWidget(self.tbInitTime_back)
        self.dteInitTime = QtGui.QDateTimeEdit(ProductChooserDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dteInitTime.sizePolicy().hasHeightForWidth())
        self.dteInitTime.setSizePolicy(sizePolicy)
        self.dteInitTime.setMinimumSize(QtCore.QSize(140, 0))
        self.dteInitTime.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.dteInitTime.setReadOnly(False)
        self.dteInitTime.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.dteInitTime.setCorrectionMode(QtGui.QAbstractSpinBox.CorrectToPreviousValue)
        self.dteInitTime.setCalendarPopup(False)
        self.dteInitTime.setTimeSpec(QtCore.Qt.UTC)
        self.dteInitTime.setObjectName("dteInitTime")
        self.horizontalLayout_4.addWidget(self.dteInitTime)
        self.tbInitTime_fwd = QtGui.QToolButton(ProductChooserDialog)
        self.tbInitTime_fwd.setArrowType(QtCore.Qt.RightArrow)
        self.tbInitTime_fwd.setObjectName("tbInitTime_fwd")
        self.horizontalLayout_4.addWidget(self.tbInitTime_fwd)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.buttonBox = QtGui.QDialogButtonBox(ProductChooserDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ProductChooserDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ProductChooserDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ProductChooserDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ProductChooserDialog)

    def retranslateUi(self, ProductChooserDialog):
        ProductChooserDialog.setWindowTitle(
            QtGui.QApplication.translate("ProductChooserDialog", "Product Chooser", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(
            QtGui.QApplication.translate("ProductChooserDialog", "Type:", None, QtGui.QApplication.UnicodeUTF8))
        self.cbType.setItemText(0, QtGui.QApplication.translate("ProductChooserDialog", "(type)", None,
                                                                QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(
            QtGui.QApplication.translate("ProductChooserDialog", "Product:", None, QtGui.QApplication.UnicodeUTF8))
        self.cbProduct.setItemText(0, QtGui.QApplication.translate("ProductChooserDialog", "(product)", None,
                                                                   QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(
            QtGui.QApplication.translate("ProductChooserDialog", "Region:", None, QtGui.QApplication.UnicodeUTF8))
        self.cbRegion.setItemText(0, QtGui.QApplication.translate("ProductChooserDialog", "(region)", None,
                                                                  QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ProductChooserDialog", "Initialisation:", None,
                                                          QtGui.QApplication.UnicodeUTF8))
        self.tbInitTime_back.setText(
            QtGui.QApplication.translate("ProductChooserDialog", "<<", None, QtGui.QApplication.UnicodeUTF8))
        self.dteInitTime.setDisplayFormat(
            QtGui.QApplication.translate("ProductChooserDialog", "yyyy-MM-dd hh:mm UTC", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.tbInitTime_fwd.setText(
            QtGui.QApplication.translate("ProductChooserDialog", ">>", None, QtGui.QApplication.UnicodeUTF8))
