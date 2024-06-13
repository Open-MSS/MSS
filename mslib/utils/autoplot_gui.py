import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QListWidgetItem,
                             QVBoxLayout, QPushButton, QLabel)
from mslib.msui.qt5.ui_mss_autoplot import Ui_Form
from mslib.utils.config import config_loader, read_config_file
from mslib.utils.mssautoplot import Plotting, load_from_ftml


class Layers(QWidget):
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


class Upload(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cpath = None
        self.view = None
        self.itime = None
        self.vtime = None
        self.intv = None
        self.num_interpolation_points = None
        self.num_labels = None
        self.stime = None
        self.etime = None
        self.sections = None
        self.level = None
        self.resolution = None
        self.ftrack = {}
        self.operations = {}
        self.url = []

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
        # all spinBox
        self.numinterSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.numinterSpinBox))
        self.numlabelsSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.numlabelsSpinBox))
        self.stimeSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.stimeSpinBox))
        self.etimeSpinBox.valueChanged.connect(
            lambda value: self.onSpinBoxValueChanged(value, self.etimeSpinBox))
        # all pushButton
        self.addFtrackButton.clicked.connect(self.addftrack)
        self.removeFtrackButton.clicked.connect(self.removeftrack)
        self.addOperationsButton.clicked.connect(self.addOperation)
        self.removeOperationsButton.clicked.connect(self.removeOperation)
        self.addUrlButton.clicked.connect(self.addURL)
        self.removeUrlButton.clicked.connect(self.removeURL)
        self.layersButton.clicked.connect(self.layersWindow)

    def openFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Select .json Config File", "", "JSON Files (*.json)", options=options)
        if fileName:
            self.cpath = fileName
            self.configureFromPath()

    def configureFromPath(self):
        read_config_file(self.path)
        self.configure = config_loader()
        if self.view is None:
            self.view = self.config["View"]
        if self.num_interpolation_points is None:
            self.num_interpolation_points = self.config["num_interpolation_points"]
        if self.num_labels is None:
            self.num_labels = self.config["num_labels"]
        if self.resolution is None:
            self.resolution = self.config["resolution"]
        if self.operations is None:
            self.operations = self.config["MSCOLAB_operations"]
        self.mscolaburl = self.config["default_MSCOLAB"]
        if self.view == "top":
            sec = "automated_plotting_hsecs"
        if self.view == "side":
            sec = "automated_plotting_vsecs"
        if self.url is None:
            self.url = self.config[sec][0]
        if self.level is None:
            self.level = self.config[sec][2]
        self.styles = self.config[sec][1]

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

    def onSpinBoxValueChanged(self, value, spinName):
        spinBoxName = spinName.objectName()
        if spinBoxName == "numinterSpinBox":
            self.num_interpolation_points = value
        if spinBoxName == "numlabelsSpinBox":
            self.num_labels = value
        if spinBoxName == "stimeSpinBox":
            self.stime = value
        if spinBoxName == "etimeSpinBox":
            self.etime = value

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
            item = QListWidgetItem(text)
            self.urlListWidget.addItem(item)
            self.urlLineEdit.clear()
            self.url.append(text)

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
    # print(window.cpath)
    # print(window.view)
    # print(window.itime)
    # print(window.vtime)
    # print(window.level)
    # print(window.stime)
    # print(window.etime)
    # print(window.intv)
    # print(window.num_interpolation_points)
    # print(window.num_labels)
    # print(window.sections)
    # print(window.resolution)
    # print(window.ftrack)
    # print(window.operations)
    # print(window.url)


if __name__ == "__main__":
    main()
