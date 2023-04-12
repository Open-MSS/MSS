# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mscolab_profile_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProfileWindow(object):
    def setupUi(self, ProfileWindow):
        ProfileWindow.setObjectName("ProfileWindow")
        ProfileWindow.resize(361, 168)
        self.gridLayout = QtWidgets.QGridLayout(ProfileWindow)
        self.gridLayout.setObjectName("gridLayout")
        self.gravatarVl = QtWidgets.QVBoxLayout()
        self.gravatarVl.setObjectName("gravatarVl")
        self.gravatarLabel = QtWidgets.QLabel(ProfileWindow)
        self.gravatarLabel.setText("")
        self.gravatarLabel.setPixmap(QtGui.QPixmap(":/gravatars/default-gravatars/default.png"))
        self.gravatarLabel.setScaledContents(True)
        self.gravatarLabel.setObjectName("gravatarLabel")
        self.gravatarVl.addWidget(self.gravatarLabel, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.gridLayout.addLayout(self.gravatarVl, 0, 2, 2, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(ProfileWindow)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 2, 1, 1, QtCore.Qt.AlignRight)
        self.deleteAccountBtn = QtWidgets.QPushButton(ProfileWindow)
        self.deleteAccountBtn.setAutoDefault(False)
        self.deleteAccountBtn.setObjectName("deleteAccountBtn")
        self.gridLayout.addWidget(self.deleteAccountBtn, 2, 0, 1, 1, QtCore.Qt.AlignLeft)
        self.infoGl = QtWidgets.QGridLayout()
        self.infoGl.setObjectName("infoGl")
        self.usernameLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.usernameLabel_2.setText("")
        self.usernameLabel_2.setObjectName("usernameLabel_2")
        self.infoGl.addWidget(self.usernameLabel_2, 0, 2, 1, 1)
        self.emailLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.emailLabel_2.setText("")
        self.emailLabel_2.setObjectName("emailLabel_2")
        self.infoGl.addWidget(self.emailLabel_2, 1, 2, 1, 1)
        self.mscolabURLLabel = QtWidgets.QLabel(ProfileWindow)
        self.mscolabURLLabel.setObjectName("mscolabURLLabel")
        self.infoGl.addWidget(self.mscolabURLLabel, 2, 0, 1, 1)
        self.mscolabURLLabel_2 = QtWidgets.QLabel(ProfileWindow)
        self.mscolabURLLabel_2.setText("")
        self.mscolabURLLabel_2.setObjectName("mscolabURLLabel_2")
        self.infoGl.addWidget(self.mscolabURLLabel_2, 2, 2, 1, 1)
        self.emailLabel = QtWidgets.QLabel(ProfileWindow)
        self.emailLabel.setObjectName("emailLabel")
        self.infoGl.addWidget(self.emailLabel, 1, 0, 1, 1)
        self.usernameLabel = QtWidgets.QLabel(ProfileWindow)
        self.usernameLabel.setObjectName("usernameLabel")
        self.infoGl.addWidget(self.usernameLabel, 0, 0, 1, 1)
        self.label = QtWidgets.QLabel(ProfileWindow)
        self.label.setObjectName("label")
        self.infoGl.addWidget(self.label, 0, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.label_2 = QtWidgets.QLabel(ProfileWindow)
        self.label_2.setObjectName("label_2")
        self.infoGl.addWidget(self.label_2, 1, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.label_3 = QtWidgets.QLabel(ProfileWindow)
        self.label_3.setObjectName("label_3")
        self.infoGl.addWidget(self.label_3, 2, 1, 1, 1, QtCore.Qt.AlignLeft)
        self.gridLayout.addLayout(self.infoGl, 0, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(ProfileWindow)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 1, 1, 1)

        self.retranslateUi(ProfileWindow)
        QtCore.QMetaObject.connectSlotsByName(ProfileWindow)

    def retranslateUi(self, ProfileWindow):
        _translate = QtCore.QCoreApplication.translate
        ProfileWindow.setWindowTitle(_translate("ProfileWindow", "MSColab Profile"))
        self.deleteAccountBtn.setText(_translate("ProfileWindow", "Delete Account"))
        self.mscolabURLLabel.setText(_translate("ProfileWindow", "Mscolab"))
        self.emailLabel.setText(_translate("ProfileWindow", "Email"))
        self.usernameLabel.setText(_translate("ProfileWindow", "Name"))
        self.label.setText(_translate("ProfileWindow", ":"))
        self.label_2.setText(_translate("ProfileWindow", ":"))
        self.label_3.setText(_translate("ProfileWindow", ":"))
        self.pushButton.setText(_translate("ProfileWindow", "Upload Image"))

from . import resources_rc
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ProfileWindow = QtWidgets.QDialog()
    ui = Ui_ProfileWindow()
    ui.setupUi(ProfileWindow)
    ProfileWindow.show()
    sys.exit(app.exec_())
