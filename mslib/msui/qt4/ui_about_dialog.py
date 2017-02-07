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
        AboutMSUIDialog.resize(1104, 551)
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
        self.textBrowser = QtGui.QTextBrowser(AboutMSUIDialog)
        self.textBrowser.setMaximumSize(QtCore.QSize(1310, 192))
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        spacerItem1 = QtGui.QSpacerItem(20, 6, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.lblVersion = QtGui.QLabel(AboutMSUIDialog)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.verticalLayout.addWidget(self.lblVersion)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.label_7 = QtGui.QLabel(AboutMSUIDialog)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.verticalLayout.addWidget(self.label_7)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.label_3 = QtGui.QLabel(AboutMSUIDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout.addWidget(self.label_3)
        self.label_4 = QtGui.QLabel(AboutMSUIDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.label_5 = QtGui.QLabel(AboutMSUIDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.verticalLayout.addWidget(self.label_5)
        spacerItem4 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem4)
        self.label_6 = QtGui.QLabel(AboutMSUIDialog)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.verticalLayout.addWidget(self.label_6)
        spacerItem5 = QtGui.QSpacerItem(20, 7, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem5)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem6 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem6)
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
        self.textBrowser.setHtml(_translate("AboutMSUIDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans Mono\'; color:#000000; background-color:#ffffff;\">Please read the reference documentation:</span><span style=\" font-family:\'DejaVu Sans Mono\'; color:#000000;\"><br /><br />Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based tool to plan<br />atmospheric research flights, Geosci. Model Dev., 5,55-71, doi:10.5194/gmd-5-55-2012, 2012.<br /><br />and the paper\'s Supplement (which includes a tutorial) before using the application. The documents are available at:<br /><br /> * </span><span style=\" font-family:\'DejaVu Sans Mono\'; color:#000000; background-color:#ffffff;\">http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012.pdf</span><span style=\" font-family:\'DejaVu Sans Mono\'; color:#000000;\"><br /> * http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012-supplement.pdf<br /><br />When using this software, please be so kind and acknowledge its use by citing the above mentioned reference documentation in publications, presentations, reports, etc. that you create. Thank you very much.<br /><br /></span></p></body></html>", None))
        self.lblVersion.setText(_translate("AboutMSUIDialog", "Version: --VERSION--", None))
        self.label_7.setText(_translate("AboutMSUIDialog", "License: Apache License Version 2.0", None))
        self.label_3.setText(_translate("AboutMSUIDialog", "Copyright 2008-2014: Deutsches Zentrum fuer Luft- und Raumfahrt e.V.", None))
        self.label_4.setText(_translate("AboutMSUIDialog", "Copyright 2011-2014: Marc Rautenhaus", None))
        self.label_5.setText(_translate("AboutMSUIDialog", "Copyright 2015-2016: Marc Rautenhaus, Isabell Krisch, Jörn Ungermann, Jens-Uwe Grooß, Thomas Breuer, Reimar Bauer", None))
        self.label_6.setText(_translate("AboutMSUIDialog", "<html><head/><body><p>See <a href=\"http://mss.rtfd.io\"><span style=\" text-decoration: underline; color:#0000ff;\">http://mss.rtfd.io</span></a> for details.</p></body></html>", None))
        self.btOK.setText(_translate("AboutMSUIDialog", "Ok", None))

