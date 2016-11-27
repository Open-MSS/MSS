"""Control widget to configure remote sensing overlays.


This file is part of the Mission Support System User Interface (MSUI).

AUTHORS:
========

* Joern Ungermann

"""

from PyQt4 import QtGui, QtCore  # Qt4 bindings
from mslib.msui import ui_remotesensing_dockwidget as ui


class RemoteSensingControlWidget(QtGui.QWidget, ui.Ui_RemoteSensingDockWidget):
    """This class implements the remote sensing functionality as dockable widget.
    """

    def __init__(self, parent=None, view=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        view -- reference to mpl canvas class
        """
        super(RemoteSensingControlWidget, self).__init__(parent)
        self.setupUi(self)

        self.view = view

        button = self.btTangentsColour
        palette = QtGui.QPalette(button.palette())
        colour = QtGui.QColor()
        colour.setRgbF(1, 0, 0, 1)
        palette.setColor(QtGui.QPalette.Button, colour)
        button.setPalette(palette)

        self.dsbTangentHeight.setValue(10.)
        self.dteStartTime.setDate(QtCore.QDate.currentDate())
        self.dteStartTime.setTime(QtCore.QTime.currentTime())

        # update plot on every value change
        self.cbDrawTangents.stateChanged.connect(self.update_settings)
        self.cbShowSolarAngle.stateChanged.connect(self.update_settings)
        self.connect(self.btTangentsColour, QtCore.SIGNAL("clicked()"), self.set_tangentpoint_colour)

        self.dsbTangentHeight.valueChanged.connect(self.update_settings)
        self.dteStartTime.dateTimeChanged.connect(self.update_settings)

        self.update_settings()

    def update_settings(self):
        settings = {
            "draw_tangents": self.cbDrawTangents.isChecked(),
            "tangent_height": self.dsbTangentHeight.value(),
            "show_solar_angle": self.cbShowSolarAngle.isChecked(),
            "start_time": self.dteStartTime.dateTime().toPyDateTime(),
            "colour_tangents":
                QtGui.QPalette(self.btTangentsColour.palette()).color(
                    QtGui.QPalette.Button).getRgbF()
        }
        self.view.setRemoteSensingAppearance(settings)

    def set_tangentpoint_colour(self):
        """Slot for the colour buttons: Opens a QColorDialog and sets the
           new button face colour.
        """
        button = self.btTangentsColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtGui.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.update_settings()