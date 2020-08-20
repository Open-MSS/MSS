# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mslib/msui/ui/ui_mscolab_help_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_mscolabHelpDialog(object):
    def setupUi(self, mscolabHelpDialog):
        mscolabHelpDialog.setObjectName("mscolabHelpDialog")
        mscolabHelpDialog.resize(734, 597)
        self.gridLayout = QtWidgets.QGridLayout(mscolabHelpDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.mscolabHelpTabWidget = QtWidgets.QTabWidget(mscolabHelpDialog)
        self.mscolabHelpTabWidget.setObjectName("mscolabHelpTabWidget")
        self.connecting = QtWidgets.QWidget()
        self.connecting.setObjectName("connecting")
        self.label = QtWidgets.QLabel(self.connecting)
        self.label.setGeometry(QtCore.QRect(200, 0, 301, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_3 = QtWidgets.QLabel(self.connecting)
        self.label_3.setGeometry(QtCore.QRect(120, 80, 471, 51))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap("../resources/mscolab-help/connect.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.label_5 = QtWidgets.QLabel(self.connecting)
        self.label_5.setGeometry(QtCore.QRect(190, 220, 331, 191))
        self.label_5.setText("")
        self.label_5.setPixmap(QtGui.QPixmap("../resources/mscolab-help/add-user.png"))
        self.label_5.setScaledContents(True)
        self.label_5.setObjectName("label_5")
        self.textEdit_5 = QtWidgets.QTextEdit(self.connecting)
        self.textEdit_5.setGeometry(QtCore.QRect(0, 30, 691, 31))
        self.textEdit_5.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_5.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_5.setReadOnly(True)
        self.textEdit_5.setObjectName("textEdit_5")
        self.textEdit_6 = QtWidgets.QTextEdit(self.connecting)
        self.textEdit_6.setGeometry(QtCore.QRect(0, 170, 691, 41))
        self.textEdit_6.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_6.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_6.setReadOnly(True)
        self.textEdit_6.setObjectName("textEdit_6")
        self.textEdit_7 = QtWidgets.QTextEdit(self.connecting)
        self.textEdit_7.setEnabled(True)
        self.textEdit_7.setGeometry(QtCore.QRect(0, 470, 691, 31))
        self.textEdit_7.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_7.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_7.setUndoRedoEnabled(False)
        self.textEdit_7.setReadOnly(True)
        self.textEdit_7.setObjectName("textEdit_7")
        self.mscolabHelpTabWidget.addTab(self.connecting, "")
        self.creating_project = QtWidgets.QWidget()
        self.creating_project.setObjectName("creating_project")
        self.label_7 = QtWidgets.QLabel(self.creating_project)
        self.label_7.setGeometry(QtCore.QRect(20, 0, 601, 31))
        self.label_7.setText("")
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.creating_project)
        self.label_8.setGeometry(QtCore.QRect(170, 60, 331, 151))
        self.label_8.setText("")
        self.label_8.setPixmap(QtGui.QPixmap(":/images/mscolab-help/add-project.png"))
        self.label_8.setScaledContents(True)
        self.label_8.setObjectName("label_8")
        self.label_11 = QtWidgets.QLabel(self.creating_project)
        self.label_11.setGeometry(QtCore.QRect(50, 430, 581, 21))
        self.label_11.setText("")
        self.label_11.setObjectName("label_11")
        self.textEdit_3 = QtWidgets.QTextEdit(self.creating_project)
        self.textEdit_3.setGeometry(QtCore.QRect(0, 20, 691, 41))
        self.textEdit_3.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_3.setReadOnly(True)
        self.textEdit_3.setObjectName("textEdit_3")
        self.textEdit_4 = QtWidgets.QTextEdit(self.creating_project)
        self.textEdit_4.setGeometry(QtCore.QRect(0, 220, 691, 81))
        self.textEdit_4.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_4.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_4.setReadOnly(True)
        self.textEdit_4.setObjectName("textEdit_4")
        self.mscolabHelpTabWidget.addTab(self.creating_project, "")
        self.collaborating = QtWidgets.QWidget()
        self.collaborating.setObjectName("collaborating")
        self.textEdit_8 = QtWidgets.QTextEdit(self.collaborating)
        self.textEdit_8.setEnabled(True)
        self.textEdit_8.setGeometry(QtCore.QRect(0, 330, 691, 41))
        self.textEdit_8.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_8.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_8.setUndoRedoEnabled(False)
        self.textEdit_8.setReadOnly(True)
        self.textEdit_8.setObjectName("textEdit_8")
        self.textEdit_9 = QtWidgets.QTextEdit(self.collaborating)
        self.textEdit_9.setEnabled(True)
        self.textEdit_9.setGeometry(QtCore.QRect(0, 190, 691, 41))
        self.textEdit_9.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_9.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_9.setUndoRedoEnabled(False)
        self.textEdit_9.setReadOnly(True)
        self.textEdit_9.setObjectName("textEdit_9")
        self.textEdit_10 = QtWidgets.QTextEdit(self.collaborating)
        self.textEdit_10.setEnabled(True)
        self.textEdit_10.setGeometry(QtCore.QRect(0, 0, 691, 61))
        self.textEdit_10.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_10.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_10.setUndoRedoEnabled(False)
        self.textEdit_10.setReadOnly(True)
        self.textEdit_10.setObjectName("textEdit_10")
        self.mscolabHelpTabWidget.addTab(self.collaborating, "")
        self.working_on_project = QtWidgets.QWidget()
        self.working_on_project.setObjectName("working_on_project")
        self.textEdit_11 = QtWidgets.QTextEdit(self.working_on_project)
        self.textEdit_11.setGeometry(QtCore.QRect(0, 440, 691, 61))
        self.textEdit_11.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_11.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_11.setReadOnly(True)
        self.textEdit_11.setObjectName("textEdit_11")
        self.textEdit_12 = QtWidgets.QTextEdit(self.working_on_project)
        self.textEdit_12.setGeometry(QtCore.QRect(0, 210, 691, 91))
        self.textEdit_12.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_12.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_12.setReadOnly(True)
        self.textEdit_12.setObjectName("textEdit_12")
        self.textEdit_13 = QtWidgets.QTextEdit(self.working_on_project)
        self.textEdit_13.setGeometry(QtCore.QRect(0, 0, 691, 71))
        self.textEdit_13.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_13.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.textEdit_13.setReadOnly(True)
        self.textEdit_13.setObjectName("textEdit_13")
        self.mscolabHelpTabWidget.addTab(self.working_on_project, "")
        self.verticalLayout.addWidget(self.mscolabHelpTabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(mscolabHelpDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(mscolabHelpDialog)
        self.mscolabHelpTabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(mscolabHelpDialog.accept)
        self.buttonBox.rejected.connect(mscolabHelpDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(mscolabHelpDialog)

    def retranslateUi(self, mscolabHelpDialog):
        _translate = QtCore.QCoreApplication.translate
        mscolabHelpDialog.setWindowTitle(_translate("mscolabHelpDialog", "Help"))
        self.label.setText(_translate("mscolabHelpDialog", "Welcome to Mission Support Collaboration!"))
        self.textEdit_5.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1. To get started, enter your mscolab server url and press connect.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.textEdit_6.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2. If you\'re using mscolab for the first time, click on the <span style=\" font-weight:600;\">&quot;Add User&quot;</span> button after connecting and register yourself by filling the required details.</p></body></html>"))
        self.textEdit_7.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">You\'re now ready to start using mscolab!</p></body></html>"))
        self.mscolabHelpTabWidget.setTabText(self.mscolabHelpTabWidget.indexOf(self.connecting), _translate("mscolabHelpDialog", "Connecting"))
        self.textEdit_3.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1. Each flight track in mscolab is called a <span style=\" font-weight:600;\">&quot;Project&quot;</span>. You can create your project by clicking on the <span style=\" font-weight:600;\">&quot;Add Project&quot;</span> button and filling in the required details.</p></body></html>"))
        self.textEdit_4.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2. The project list shows all the projects you have access to along with your access level to the project. There are <span style=\" font-weight:600;\">4 access levels</span> you can have to a project. These are - Creator, Admin, Collaborator and Viewer.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">3. You can select a project by <span style=\" font-weight:600;\">double-clicking</span> on it in the project list and then start working on it.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">4. Select a project and you can start editing the flight track in 3 different views - Top, Side and Table.</p></body></html>"))
        self.mscolabHelpTabWidget.setTabText(self.mscolabHelpTabWidget.indexOf(self.creating_project), _translate("mscolabHelpDialog", "Creating Project"))
        self.textEdit_8.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">3. Keep track of all the changes made to your project by opening the version history window using the <span style=\" font-weight:600;\">&quot;Version History&quot;</span> button. Save your progress by giving version names and quickly revert back to a version by using the &quot;Checkout&quot; button in the window.</p></body></html>"))
        self.textEdit_9.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2. You can chat with all the users added to a project by opening the chat window using the <span style=\" font-weight:600;\">&quot;Chat&quot;</span> button. The chart supports media upload, message delete, message reply and markdown formatting.</p></body></html>"))
        self.textEdit_10.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1. To collaborate with other users, you can add them to a project if you are the creator of the project or have administrator access. Click on the <span style=\" font-weight:600;\">&quot;Manage Users&quot;</span> button after selecting the project and you can quickly add new users and update or delete the access of existing users.</p></body></html>"))
        self.mscolabHelpTabWidget.setTabText(self.mscolabHelpTabWidget.indexOf(self.collaborating), _translate("mscolabHelpDialog", "Collaborating"))
        self.textEdit_11.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">You can toggle between these modes at any moment you like. All your local changes are saved on your machine and are not discarded. You can uncheck the <span style=\" font-weight:600;\">&quot;Work Locally&quot;</span> checkbox at any time, work on the shared file and then turn it back on and continue from where you left off.</p></body></html>"))
        self.textEdit_12.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">2. If you just want to try some changes on your own and not share with everyone else, you can turn the <span style=\" font-weight:600;\">&quot;Work Locally&quot; </span>checkbox <span style=\" font-weight:600;\">on</span>. In work locally mode your changes are kept on your machine and not shared with anyone. Once you\'re done making changes you can use the <span style=\" font-weight:600;\">&quot;Save to Server&quot;</span> button to save your changes with everyone. You can also use the <span style=\" font-weight:600;\">&quot;Fetch from Server&quot; </span>button so you can merge the shared flight track data with your local data.</p></body></html>"))
        self.textEdit_13.setHtml(_translate("mscolabHelpDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">While working on a project you can be working in 2 modes:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1. When the <span style=\" font-weight:600;\">&quot;Work Locally&quot; </span>checkbox is <span style=\" font-weight:600;\">unchecked, </span>you\'re in the default mode. In this mode all your changes will be shared with all other users in real-time. Each change made can also be viewed in the version history window in this mode.</p></body></html>"))
        self.mscolabHelpTabWidget.setTabText(self.mscolabHelpTabWidget.indexOf(self.working_on_project), _translate("mscolabHelpDialog", "Working on Project"))

import resources_rc
