"""Common PyQt4-derived classes and methods required by all MSS UI
   modules.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from abc import abstractmethod

# related third party imports
from mslib.msui.mss_qt import QtGui, QtCore


# local application imports

class MSSViewWindow(QtGui.QMainWindow):
    """Derives QMainWindow to provide some common functionality to all
       MSUI view windows.
    """
    name = "Abstract MSS View Window"
    identifier = None

    viewCloses = QtCore.pyqtSignal(name="viewCloses")

    def __init__(self, parent=None, model=None):
        super(MSSViewWindow, self).__init__(parent)

        # Object variables:
        self.waypoints_model = model  # pointer to the current flight track.

        # List that accommodates the dock window instances: Needs to be defined
        # in proper size in derived classes!
        self.docks = []

    def closeEvent(self, event):
        """Ask user if he/she wants to close the window.

        Overloads QtGui.QMainWindow.closeEvent(). This method is called if
        Qt receives a window close request for our application window.
        """
        ret = QtGui.QMessageBox.warning(self, self.tr("Mission Support System"),
                                        self.tr("Do you want to close this %s?" % self.name),
                                        QtGui.QMessageBox.Yes,
                                        QtGui.QMessageBox.No | QtGui.QMessageBox.Default)
        if ret == QtGui.QMessageBox.Yes:
            self.viewCloses.emit()
            event.accept()
        else:
            event.ignore()

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance that the view displays.
        """
        self.waypoints_model = model

    def controlToBeCreated(self, index):
        """Check if the dock widget at index <index> exists. If yes, show
           the widget and return -1. Otherwise return <index-1>.
        """
        index -= 1
        if index >= 0:
            if self.docks[index]:
                # The widget has already been created, but is not visible at
                # the moment.
                self.docks[index].show()
                self.docks[index].raise_()
                index = -1
        if hasattr(self, "cbTools"):
            self.cbTools.setCurrentIndex(0)
        return index

    def createDockWidget(self, index, title, widget):
        """Create a new dock widget. A pointer to the dock widget will be
           stored in self.docks[index]. The dock will have the title <title>
           and contain the Qt widget <widget>.
        """
        self.docks[index] = QtGui.QDockWidget(title, self)
        self.docks[index].setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        # setWidget transfers the widget's ownership to Qt -- no setParent()
        # call is necessary:
        self.docks[index].setWidget(widget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.docks[index])

        # Check if another dock widget occupies the dock area. If yes,
        # tabbify the old and the new widget.
        for dock in self.docks:
            if dock and not dock == self.docks[index] and not dock.isFloating():
                self.tabifyDockWidget(dock, self.docks[index])
                break
        self.docks[index].show()
        self.docks[index].raise_()

    @abstractmethod
    def getView(self):
        """Return view object that tools can interact with.

        ABSTRACT method, needs to be implemented in derived classes.
        """
        return None

    def setIdentifier(self, identifier):
        self.identifier = identifier


class MSSMplViewWindow(MSSViewWindow):
    """Adds Matplotlib-specific functionality to MSSViewWindow.
    """

    def __init__(self, parent=None, model=None):
        super(MSSMplViewWindow, self).__init__(parent, model)
        self.mpl = None

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance that the view displays.
        """
        self.waypoints_model = model
        if self.mpl:
            self.mpl.canvas.setWaypointsModel(model)

    def getView(self):
        """Return the MplCanvas instance of the window.
        """
        return self.mpl.canvas
