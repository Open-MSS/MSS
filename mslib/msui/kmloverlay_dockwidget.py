"""
AUTHORS:
========

* Joern Ungermann (ju)

"""

# related third party imports
import logging
import os
import pykml.parser

# local application imports
from mslib.msui.mss_qt import QtGui, QtWidgets, USE_PYQT5
from mslib.msui.mss_qt import ui_kmloverlay_dockwidget as ui
from mslib.msui.mpl_map import KMLPatch
from mslib.mss_util import save_settings_pickle, load_settings_pickle


class KMLOverlayControlWidget(QtWidgets.QWidget, ui.Ui_KMLOverlayDockWidget):
    """
    This class provides the interface for accessing KML files and
    adding the appropriate patches to the TopView canvas.
    """
    def __init__(self, parent=None, view=None):
        super(KMLOverlayControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view
        self.kml = None
        self.patch = None

        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.select_file)
        self.btLoadFile.clicked.connect(self.load_file)
        self.pbSelectColour.clicked.connect(self.select_colour)
        self.cbOverlay.stateChanged.connect(self.update_settings)
        self.dsbLineWidth.valueChanged.connect(self.update_settings)
        self.cbManualStyle.stateChanged.connect(self.update_settings)

        self.cbOverlay.setChecked(True)
        self.cbOverlay.setEnabled(False)
        self.cbManualStyle.setChecked(False)

        self.settings_tag = "kmldock"
        settings = load_settings_pickle(
            self.settings_tag, {"filename": "", "linewidth": 1, "colour": (0, 0, 0, 1)})

        self.leFile.setText(settings["filename"])
        self.dsbLineWidth.setValue(settings["linewidth"])

        palette = QtGui.QPalette(self.pbSelectColour.palette())
        colour = QtGui.QColor()
        colour.setRgbF(*settings["colour"])
        palette.setColor(QtGui.QPalette.Button, colour)
        self.pbSelectColour.setPalette(palette)

    def __del__(self):
        settings = {
            "filename": unicode(self.leFile.text()),
            "linewidth": self.dsbLineWidth.value(),
            "colour": self.get_color()
        }
        save_settings_pickle(self.settings_tag, settings)

    def get_color(self):
        button = self.pbSelectColour
        return QtGui.QPalette(button.palette()).color(QtGui.QPalette.Button).getRgbF()

    def update_settings(self):
        """
        Called when the visibility checkbox is toggled and hides/shows
        the overlay if loaded.
        """
        if self.view is not None and self.cbOverlay.isChecked() and self.patch is not None:
            self.view.plotKML(self.patch)
            self.patch.update(self.cbManualStyle.isChecked(), self.get_color(), self.dsbLineWidth.value())
        elif self.patch is not None:
            self.view.plotKML(None)

    def select_colour(self):
        button = self.pbSelectColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.update_settings()

    def select_file(self):
        """Slot that opens a file dialog to choose a file with satellite
           overpass predictions.
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open KML Polygonal File", os.path.dirname(unicode(self.leFile.text())), "(*.kml)")
        filename = filename[0] if USE_PYQT5 else unicode(filename)

        if not filename:
            return
        self.leFile.setText(filename)

    def load_file(self):
        """
        Loads an KML file selected by the leFile box and constructs the
        corresponding patch.
        """
        if self.patch is not None:
            self.patch.remove()
            self.view.plotKML(None)
            self.patch = None
            self.cbOverlay.setEnabled(False)
        try:
            with open(unicode(self.leFile.text())) as kmlf:
                self.kml = pykml.parser.parse(kmlf).getroot()
                self.patch = KMLPatch(self.view.map, self.kml,
                                      self.cbManualStyle.isChecked(), self.get_color(), self.dsbLineWidth.value())
            self.cbOverlay.setEnabled(True)
            if self.view is not None and self.cbOverlay.isChecked():
                self.view.plotKML(self.patch)
        except (IOError, pykml.parser.etree.XMLSyntaxError), ex:
            logging.error("KML Overlay - %s: %s", type(ex), ex)
            QtWidgets.QMessageBox.critical(
                self, self.tr("KML Overlay"), self.tr(u"ERROR:\n{}\n{}".format(type(ex), ex)))
