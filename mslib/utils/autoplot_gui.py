import sys
import click
import requests
import keyring
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QListWidgetItem,
                             QVBoxLayout, QPushButton, QLabel)
from mslib.msui.qt5.ui_mss_autoplot import Ui_Form
from mslib.msui.qt5.ui_wms_login import Ui_Form2
from mslib.utils import config as conf
from mslib.utils.mssautoplot import main as autopl
from mslib.msui.mscolab import MSColab_ConnectDialog, MSUIMscolab
from mslib.utils.auth import save_password_to_keyring


class Layers(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Layers Window')
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()

        self.label = QLabel('Select Layers Under development', self)
        layout.addWidget(self.label)

        self.closeButton = QPushButton('Close', self)
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.closeButton)

        self.setLayout(layout)


class WmsLoginInfo(QWidget, Ui_Form2):
    def __init__(self, link):
        super().__init__()
        self.setupUi(self)
        self.savePushButton.clicked.connect(lambda: self.funct(link))

    def funct(self, link):
        wms = link
        usern = self.userNameLineEdit.text()
        passw = self.passwordLineEdit.text()
        save_password_to_keyring(service_name=wms, username=usern, password=passw)
        self.close()


class Upload(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cpath = None
        self.view = "top"
        self.itime = None
        self.vtime = None
        self.intv = None
        self.stime = None
        self.etime = None
        self.ftrack = {}
        self.sections = None
        self.vertical = None

        self.url = []
        self.layer = None
        self.styles = None
        self.level = None

        self.num_interpolation_points = None
        self.num_labels = None
        self.resolution = None
        self.mscolaburl = None
        self.operations = {}

        # cpath
        self.cpathButton.clicked.connect(self.openFileDialog)

        # all QcomboBox
        self.viewComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.viewComboBox))
        self.sectionsComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.sectionsComboBox))
        self.resolutionComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.resolutionComboBox))
        self.itimeComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.itimeComboBox))
        self.vtimeComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.vtimeComboBox))
        self.intvComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.intvComboBox))
        self.levelComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.levelComboBox))
        self.stimeComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.stimeComboBox))
        self.etimeComboBox.currentIndexChanged.connect(
            lambda: self.comboBoxInput(self.etimeComboBox))

        # all spinBox
        self.numinterSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.numinterSpinBox))
        self.numlabelsSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.numlabelsSpinBox))

        # all pushButton
        self.addFtrackButton.clicked.connect(self.addftrack)
        self.removeFtrackButton.clicked.connect(self.removeftrack)
        self.addOperationsButton.clicked.connect(self.addOperation)
        self.removeOperationsButton.clicked.connect(self.removeOperation)
        self.addUrlButton.clicked.connect(self.addURL)
        self.removeUrlButton.clicked.connect(self.removeURL)
        self.layersButton.clicked.connect(self.layersWindow)
        self.storePlotsButton.clicked.connect(self.storePlots)

    def openFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", "", "JSON Files (*.json)", options=options)
        if fileName:
            self.cpath = fileName
            self.configureFromPath(self.cpath)

    def configureFromPath(self, path):
        conf.read_config_file(path)
        configure = conf.config_loader()
        if self.view == "linear":
            sec = "automated_plotting_lsecs"
        elif self.view == "side":
            sec = "automated_plotting_vsecs"
        else:
            sec = "automated_plotting_hsecs"

        self.ftrack[configure["automated_plotting_flights"][0][0]] = configure["automated_plotting_flights"][0][3]
        self.flight = configure["automated_plotting_flights"][0][0]
        self.fname = configure["automated_plotting_flights"][0][3]
        self.sections = configure["automated_plotting_flights"][0][1]
        self.vertical = configure["automated_plotting_flights"][0][2]
        self.itime = configure["automated_plotting_flights"][0][4]

        self.url.append(configure[sec][0][0])
        self.layer = configure[sec][0][1]
        self.styles = configure[sec][0][2]
        self.level = configure[sec][0][3]

    def storePlots(self):
        args = [
            "--cpath", self.cpath,
            "--view", self.view,
            "--ftrack", next(iter(self.ftrack.values())),
            "--itime", self.itime,
            "--vtime", self.vtime,
            "--intv", self.intv,
            "--stime", self.stime,
            "--etime", self.etime
        ]
        with click.Context(autopl):
            autopl.main(args=args, prog_name="autoplot_gui")

    def comboBoxInput(self, combo):
        comboBoxName = combo.objectName()
        if comboBoxName == "sectionsComboBox":
            self.sections = self.sectionsComboBox.currentText()
        if comboBoxName == "viewComboBox":
            self.view = self.viewComboBox.currentText()
        if comboBoxName == "resolutionComboBox":
            self.resolution = self.resolutionComboBox.currentText()
        if comboBoxName == "levelComboBox":
            self.level = self.levelComboBox.currentText()
        if comboBoxName == "itimeComboBox":
            self.itime = self.itimeComboBox.currentText()
        if comboBoxName == "vtimeComboBox":
            self.vtime = self.vtimeComboBox.currentText()
        if comboBoxName == "intvComboBox":
            self.intv = self.intvComboBox.currentText()
        if comboBoxName == "stimeComboBox":
            self.stime = self.stimeComboBox.currentText()
        if comboBoxName == "etimeComboBox":
            self.etime = self.etimeComboBox.currentText()

    def onSpinBoxValueChanged(self, value, spinName):
        spinBoxName = spinName.objectName()
        if spinBoxName == "numinterSpinBox":
            self.num_interpolation_points = value
        if spinBoxName == "numlabelsSpinBox":
            self.num_labels = value

    def addftrack(self):
        text = self.flightLineEdit.text()
        if text:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Select .ftml flights File", "", "ftml Files (*.ftml)", options=options)
            path = fileName
            if path:
                self.ftrack[text] = path
                item = QListWidgetItem(text)
                self.flightListWidget.addItem(item)
            self.flightLineEdit.clear()

    def removeftrack(self):
        selected = self.flightListWidget.selectedItems()
        if selected:
            for i in selected:
                del self.ftrack[i.text()]
                self.flightListWidget.takeItem(self.flightListWidget.row(i))

    def addOperation(self):
        text = self.operationsLineEdit.text()
        if text:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Select Operations File", "", "JSON Files (*.json)", options=options)
            path = fileName
            if path:
                self.operations[text] = path
                item = QListWidgetItem(text)
                self.operationsListWidget.addItem(item)
            self.operationsLineEdit.clear()

    def removeOperation(self):
        selected = self.operationsListWidget.selectedItems()
        if selected:
            for i in selected:
                del self.operations[i.text()]
                self.operationsListWidget.takeItem(self.operationsListWidget.row(i))

    def addURL(self):
        text = self.urlLineEdit.text()
        if text:
            response = requests.get(text)
            if response.status_code == 401:
                self.check_url_in_keyring(text)
            else:
                self.urlListWidget.addItem(QListWidgetItem(text))
                self.urlLineEdit.clear()
                self.url.append(text)

    def check_url_in_keyring(self, link):
        cred = keyring.get_credential(link, "")

        if cred:
            check = self.check_website_access(link, cred.username, cred.password)
            if check == True:
                self.urlListWidget.addItem(QListWidgetItem(link))
                self.urlLineEdit.clear()
                self.url.append(link)
            else:
                self.connect_dialog = WmsLoginInfo(link)
                self.connect_dialog.show()

        else:
            self.connect_dialog = WmsLoginInfo(link)
            self.connect_dialog.show()

    def check_website_access(self, link, username, password):
        try:
            response = requests.get(link, auth=requests.auth.HTTPBasicAuth(username, password))

            if response.status_code == 200:
                print("Authentication successful!")
                return True
            else:
                print(f"Failed to authenticate. Status code: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")

    def removeURL(self):
        selected = self.urlListWidget.selectedItems()
        if selected:
            for i in selected:
                self.url.remove(i.text())
                self.urlListWidget.takeItem(self.urlListWidget.row(i))

    def layersWindow(self):
        self.layerobj = Layers()
        self.layerobj.show()


def main():
    app = QApplication(sys.argv)
    window = Upload()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
