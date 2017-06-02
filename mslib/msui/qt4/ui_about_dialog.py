# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_about_dialog.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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
        AboutMSUIDialog.resize(1104, 600)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AboutMSUIDialog.sizePolicy().hasHeightForWidth())
        AboutMSUIDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(AboutMSUIDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.lblDummy = QtGui.QLabel(AboutMSUIDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDummy.sizePolicy().hasHeightForWidth())
        self.lblDummy.setSizePolicy(sizePolicy)
        self.lblDummy.setMinimumSize(QtCore.QSize(100, 40))
        self.lblDummy.setMaximumSize(QtCore.QSize(100, 40))
        self.lblDummy.setText(_fromUtf8(""))
        self.lblDummy.setObjectName(_fromUtf8("lblDummy"))
        self.horizontalLayout_3.addWidget(self.lblDummy)
        self.lblName = QtGui.QLabel(AboutMSUIDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.lblName.setFont(font)
        self.lblName.setTextFormat(QtCore.Qt.PlainText)
        self.lblName.setAlignment(QtCore.Qt.AlignCenter)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.horizontalLayout_3.addWidget(self.lblName)
        self.lblPython = QtGui.QLabel(AboutMSUIDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPython.sizePolicy().hasHeightForWidth())
        self.lblPython.setSizePolicy(sizePolicy)
        self.lblPython.setMinimumSize(QtCore.QSize(100, 40))
        self.lblPython.setMaximumSize(QtCore.QSize(100, 40))
        self.lblPython.setObjectName(_fromUtf8("lblPython"))
        self.horizontalLayout_3.addWidget(self.lblPython)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem)
        self.textBrowser = QtGui.QTextBrowser(AboutMSUIDialog)
        self.textBrowser.setEnabled(True)
        self.textBrowser.setMinimumSize(QtCore.QSize(0, 200))
        self.textBrowser.setMaximumSize(QtCore.QSize(1310, 300))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lblVersion = QtGui.QLabel(AboutMSUIDialog)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.horizontalLayout_2.addWidget(self.lblVersion)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        spacerItem1 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem1)
        self.lblLicense = QtGui.QLabel(AboutMSUIDialog)
        self.lblLicense.setObjectName(_fromUtf8("lblLicense"))
        self.verticalLayout_2.addWidget(self.lblLicense)
        spacerItem2 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem2)
        self.lblCopyright = QtGui.QLabel(AboutMSUIDialog)
        self.lblCopyright.setObjectName(_fromUtf8("lblCopyright"))
        self.verticalLayout_2.addWidget(self.lblCopyright)
        spacerItem3 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem3)
        self.lblLinks = QtGui.QLabel(AboutMSUIDialog)
        self.lblLinks.setOpenExternalLinks(True)
        self.lblLinks.setObjectName(_fromUtf8("lblLinks"))
        self.verticalLayout_2.addWidget(self.lblLinks)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.btOK = QtGui.QPushButton(AboutMSUIDialog)
        self.btOK.setObjectName(_fromUtf8("btOK"))
        self.horizontalLayout.addWidget(self.btOK)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.retranslateUi(AboutMSUIDialog)
        QtCore.QObject.connect(self.btOK, QtCore.SIGNAL(_fromUtf8("clicked()")), AboutMSUIDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(AboutMSUIDialog)

    def retranslateUi(self, AboutMSUIDialog):
        AboutMSUIDialog.setWindowTitle(_translate("AboutMSUIDialog", "About MSUI", None))
        self.lblName.setText(_translate("AboutMSUIDialog", "Mission Support System User Interface", None))
        self.lblPython.setText(_translate("AboutMSUIDialog", "Python Powered", None))
        self.textBrowser.setHtml(_translate("AboutMSUIDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans Mono\'; font-size:11pt; color:#000000; background-color:#ffffff;\">Please read the reference documentation:</span><span style=\" font-family:\'DejaVu Sans Mono\'; font-size:11pt; color:#000000;\"><br /><br />Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based tool to plan<br />atmospheric research flights, Geosci. Model Dev., 5,55-71, doi:10.5194/gmd-5-55-2012, 2012.<br /><br />and the paper\'s Supplement (which includes a tutorial) before using the application. The documents are available at:<br /><br /> * </span><span style=\" font-family:\'DejaVu Sans Mono\'; font-size:11pt; color:#000000; background-color:#ffffff;\">http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012.pdf</span><span style=\" font-family:\'DejaVu Sans Mono\'; font-size:11pt; color:#000000;\"><br /> * http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012-supplement.pdf<br /><br />When using this software, please be so kind and acknowledge its use by citing the above mentioned reference documentation in publications, presentations, reports, etc. that you create. Thank you very much.<br /><br /></span></p></body></html>", None))
        self.lblVersion.setText(_translate("AboutMSUIDialog", "Version: --VERSION--", None))
        self.lblLicense.setText(_translate("AboutMSUIDialog", "License: Apache License Version 2.0", None))
        self.lblCopyright.setText(_translate("AboutMSUIDialog", "Copyright 2008-2014: Deutsches Zentrum fuer Luft- und Raumfahrt e.V.\n"
"Copyright 2011-2014: Marc Rautenhaus\n"
"Copyright 2016-2017: by the mss team, see AUTHORS", None))
        self.lblLinks.setText(_translate("AboutMSUIDialog", "<html><head/><body><p>See <a href=\"http://mss.rtfd.io\"><span style=\" text-decoration: underline; color:#0000ff;\">http://mss.rtfd.io</span></a> for detailed information and documentation.<br>Report bugs or feature requests at <a href=\"https://bitbucket.org/wxmetvis/mss\"><span style=\" text-decoration: underline; color:#0000ff;\">https://bitbucket.org/wxmetvis/mss</span></a>.</p></body></html>", None))
        self.btOK.setText(_translate("AboutMSUIDialog", "Ok", None))

