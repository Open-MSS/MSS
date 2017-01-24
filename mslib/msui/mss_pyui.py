#!/usr/bin/env python
"""Mission Support System Python/Qt4 User Interface
   ================================================

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

   When using this software, please acknowledge its use by citing the
   reference documentation in any publication, presentation, report,
   etc. you create:

   Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based tool
   to plan atmospheric research flights, Geosci. Model Dev., 5, 55-71,
   doi:10.5194/gmd-5-55-2012, 2012.

********************************************************************************

This file is part of the DLR/IPA Mission Support System User Interface (MSUI).

Main window of the user interface application. Manages view and tool windows
(the user can open multiple windows) and provides functionalty to open, save,
and switch between flight tracks.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import sys
import os
import copy
import logging
import types
import importlib

from mslib import __version__
from mslib.msui import ui_mainwindow as ui
from mslib.msui import ui_about_dialog as ui_ab
from mslib.msui import flighttrack as ft
from mslib.msui import tableview
from mslib.msui import topview
from mslib.msui import sideview
from mslib.msui import timeseriesview
from mslib.msui import trajectories_tool
from mslib.msui import loopview
from mslib.msui import constants
from mslib.mss_util import config_loader
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui import plugins


# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# Add config path to PYTHONPATH so plugins located there may be found
sys.path.append(wms_login_cache.DEFAULT_CONFIG_PATH)

try:
    import view3D

    enable3D = True
except:
    enable3D = False

enableGENESI = False
if enableGENESI:
    try:
        import genesi_tool
    except:
        enableGENESI = False


print "***********************************************************************"
print "\n            Mission Support System (mss)\n"
print "***********************************************************************"
print "Documentation: http://mss.rtfd.io"
print "Version:", __version__
print "\nSystem is loading.."


"""
QActiveViewsListWidgetItem
"""


class QActiveViewsListWidgetItem(QtGui.QListWidgetItem):
    """Subclass of QListWidgetItem, represents an open view in the list of
       open views. Keeps a reference to the view instance (i.e. the window) it
       represents in the list of open views.
    """

    # Class variable to assign a unique ID to each view.
    opened_views = 0

    def __init__(self, view_window, parent=None,
                 type=QtGui.QListWidgetItem.UserType):
        """Add ID number to the title of the corresponing view window.
        """
        QActiveViewsListWidgetItem.opened_views += 1
        view_name = "(%i) %s" % (QActiveViewsListWidgetItem.opened_views,
                                 view_window.name)
        super(QActiveViewsListWidgetItem, self).__init__(view_name, parent,
                                                         type)

        view_window.setWindowTitle("(%i) %s" %
                                   (QActiveViewsListWidgetItem.opened_views,
                                    view_window.windowTitle()))
        view_window.setIdentifier(view_name)
        self.window = view_window
        self.parent = parent

    def view_destroyed(self):
        """Slot that removes this QListWidgetItem from the parent (the
           QListWidget) if the corresponding view has been deleted.
        """
        if self.parent:
            self.parent.takeItem(self.parent.row(self))
            self.parent.emit(QtCore.SIGNAL("viewsChanged()"))


"""
QFlightTrackListWidgetItem
"""


class QFlightTrackListWidgetItem(QtGui.QListWidgetItem):
    """Subclass of QListWidgetItem, represents a flight track in the list of
       open flight tracks. Keeps a reference to the flight track instance
       (i.e. the instance of WaypointsTableModel).
    """

    def __init__(self, flighttrack_model, parent=None,
                 type=QtGui.QListWidgetItem.UserType):
        """Item class for the list widget that accomodates the open flight
           tracks.

        Arguments:
        flighttrack_model -- instance of a flight track model that is
                             associated with the item
        parent -- pointer to the QListWidgetItem that accomodates this item.
                  If not None, the itemChanged() signal of the parent is
                  connected to the nameChanged() slot of this class, reacting
                  to name changes of the item.
        """
        view_name = flighttrack_model.name
        super(QFlightTrackListWidgetItem, self).__init__(view_name, parent,
                                                         type)

        self.parent = parent
        self.flighttrack_model = flighttrack_model

        if parent:
            parent.connect(parent,
                           QtCore.SIGNAL("itemChanged(QListWidgetItem *)"),
                           self.nameChanged)

    def nameChanged(self, item):
        """Slot to change the name of a flight track.
        """
        item.flighttrack_model.setName(str(item.text()))


"""
About MSUI DIALOG
"""


class MSS_AboutDialog(QtGui.QDialog, ui_ab.Ui_AboutMSUIDialog):
    """Dialog showing information about MSUI. Most of the displayed text is
       defined in the QtDesigner file.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSS_AboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.lblVersion.setText("Version: %s" % __version__)

"""
MAIN WINDOW
"""


class MSSMainWindow(QtGui.QMainWindow, ui.Ui_MSSMainWindow):
    """MSUI main window class. Provides user interface elements for managing
       flight tracks, views, and tools.
    """

    def __init__(self, *args):
        super(MSSMainWindow, self).__init__(*args)
        self.setupUi(self)
        # Disable the 3D view menu if OpenGL is not supported.
        self.action3DView.setEnabled(enable3D)
        self.actionDiscoverEarthObservationDataGENESI.setEnabled(enableGENESI)

        # Reference to the flight track that is currently displayed in the
        # views.
        self.active_flight_track = None
        self.lastSaveDir = os.getcwd()

        # Connect Qt SIGNALs:
        # ===================

        # File menu.
        self.connect(self.actionNewFlightTrack, QtCore.SIGNAL("triggered()"),
                     self.createNewFlightTrack)
        self.connect(self.actionOpenFlightTrack, QtCore.SIGNAL("triggered()"),
                     self.openFlightTrack)
        self.connect(self.actionCloseSelectedFlightTrack, QtCore.SIGNAL("triggered()"),
                     self.closeFlightTrack)
        self.connect(self.actionSaveActiveFlightTrack, QtCore.SIGNAL("triggered()"),
                     self.saveFlightTrack)
        self.connect(self.actionSaveActiveFlightTrackAs, QtCore.SIGNAL("triggered()"),
                     self.saveFlightTrackAs)

        # Views menu.
        self.connect(self.actionTopView, QtCore.SIGNAL("triggered()"),
                     self.createNewView)
        self.connect(self.actionSideView, QtCore.SIGNAL("triggered()"),
                     self.createNewView)
        self.connect(self.actionTableView, QtCore.SIGNAL("triggered()"),
                     self.createNewView)
        self.connect(self.actionLoopView, QtCore.SIGNAL("triggered()"),
                     self.createNewView)
        self.connect(self.actionTimeSeriesViewTrajectories, QtCore.SIGNAL("triggered()"),
                     self.createNewView)
        self.connect(self.action3DView, QtCore.SIGNAL("triggered()"),
                     self.createNewView)

        # Tools menu.
        self.connect(self.actionTrajectoryToolLagranto, QtCore.SIGNAL("triggered()"),
                     self.createNewTool)
        self.connect(self.actionDiscoverEarthObservationDataGENESI, QtCore.SIGNAL("triggered()"),
                     self.createNewTool)

        # Help menu.
        self.connect(self.actionAboutMSUI, QtCore.SIGNAL("triggered()"),
                     self.showAboutDlg)

        # Load Config
        self.connect(self.actionLoad_Configuration, QtCore.SIGNAL("triggered()"),
                     self.openConfigFile)

        # Flight Tracks.
        self.connect(self.listFlightTracks, QtCore.SIGNAL("itemChanged(QListWidgetItem *)"),
                     self.flightTrackNameChanged)
        self.connect(self.btSelectFlightTrack, QtCore.SIGNAL("clicked()"),
                     self.setFlightTrackActive)

        # Views.
        self.connect(self.listViews, QtCore.SIGNAL("itemActivated(QListWidgetItem *)"),
                     self.activateWindow)

        # Tools.
        self.connect(self.listTools, QtCore.SIGNAL("itemActivated(QListWidgetItem *)"),
                     self.activateWindow)

        self.addImportFilter("CSV", "csv", plugins.loadFromCSV)
        self.addExportFilter("CSV", "csv", plugins.saveToCSV)

        self.addImportFilter("FliteStar TXT", "txt", plugins.loadFromFliteStarText)
        self.addExportFilter("FliteStar TXT", "txt", plugins.saveToFliteStarText)

        import_plugins = config_loader(dataset="import_plugins", default={})
        for name in import_plugins:
            extension, module, function = import_plugins[name]
            imported_module = importlib.import_module(module)
            self.addImportFilter(name, extension, getattr(imported_module, function))

        export_plugins = config_loader(dataset="export_plugins", default={})
        for name in export_plugins:
            extension, module, function = export_plugins[name]
            imported_module = importlib.import_module(module)
            self.addExportFilter(name, extension, getattr(imported_module, function))

    def addImportFilter(self, name, extension, function):
        full_name = "actionImportFlightTrack" + name.replace(" ", "")

        if hasattr(self, full_name):
            raise ValueError("'{}' has already been set!".format(full_name))

        action = QtGui.QAction(self)
        action.setObjectName(ui._fromUtf8(full_name))
        action.setText(ui._translate("MSSMainWindow", name, None))
        self.menuImport_Flight_Track.addAction(action)

        def load_function_wrapper(self):
            filename = QtGui.QFileDialog.getOpenFileName(
                self, "Import Flight Track", "", name + " (*." + extension + ")")

            if not filename.isEmpty():
                filename = str(filename)
                ft_name, new_waypoints = function(filename)
                if not ft_name:
                    ft_name = filename
                waypoints_model = ft.WaypointsTableModel(name=ft_name, waypoints=new_waypoints)

                listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
                listitem.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                self.listFlightTracks.setCurrentItem(listitem)
                self.setFlightTrackActive()

        setattr(self, full_name, types.MethodType(load_function_wrapper, self))
        self.connect(action, QtCore.SIGNAL("triggered()"), getattr(self, full_name))

    def addExportFilter(self, name, extension, function):
        full_name = "actionExportFlightTrack" + name.replace(" ", "")

        if hasattr(self, full_name):
            raise ValueError("'{}' has already been set!".format(full_name))

        action = QtGui.QAction(self)
        action.setObjectName(ui._fromUtf8(full_name))
        action.setText(ui._translate("MSSMainWindow", name, None))
        self.menuExport_Active_Flight_Track.addAction(action)

        def save_function_wrapper(self):
            filename = QtGui.QFileDialog.getSaveFileName(
                self, "Export Flight Track", "", name + " (*." + extension + ")")

            if not filename.isEmpty():
                filename = str(filename)
                function(filename, self.active_flight_track.name, self.active_flight_track.waypoints)

        setattr(self, full_name, types.MethodType(save_function_wrapper, self))
        self.connect(action, QtCore.SIGNAL("triggered()"), getattr(self, full_name))

    def closeEvent(self, event):
        """Ask user if he/she wants to close the application. If yes, also
           close all views that are open.

        Overloads QtGui.QMainWindow.closeEvent(). This method is called if
        Qt receives a window close request for our application window.
        """
        ret = QtGui.QMessageBox.warning(self, self.tr("Mission Support System"),
                                        self.tr("Do you want to close the Mission "
                                                "Support System application?"),
                                        QtGui.QMessageBox.Yes,
                                        QtGui.QMessageBox.No | QtGui.QMessageBox.Default)
        if ret == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def createNewView(self):
        """Method called when the user selects a new view to be opened. Creates
           a new instance of the view and adds a QActiveViewsListWidgetItem to
           the list of open views (self.listViews).
        """
        view_window = None
        if self.sender() == self.actionTopView:
            # Top view.
            view_window = topview.MSSTopViewWindow(parent=self,
                                                   model=self.active_flight_track)
        elif self.sender() == self.actionSideView:
            # Side view.
            view_window = sideview.MSSSideViewWindow(parent=self,
                                                     model=self.active_flight_track)
        elif self.sender() == self.actionTableView:
            # Table view.
            view_window = tableview.MSSTableViewWindow(parent=self,
                                                       model=self.active_flight_track)
        elif self.sender() == self.action3DView:
            # 3D view.
            view_window = view3D.MSS3DViewWindow(parent=self)
        elif self.sender() == self.actionTimeSeriesViewTrajectories:
            # Time series view.
            view_window = timeseriesview.MSSTimeSeriesViewWindow(parent=self)
        elif self.sender() == self.actionLoopView:
            # Loop view.
            # ToDo check order
            view_window = loopview.MSSLoopWindow(config_loader(dataset="loop_configuration",
                                                               default=mss_default.loop_configuration), self)
        if view_window:
            # Make sure view window will be deleted after being closed, not
            # just hidden (cf. Chapter 5 in PyQt4).
            view_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            # Open as a non-modal window.
            view_window.show()
            # Add an entry referencing the new view to the list of views.
            listitem = QActiveViewsListWidgetItem(view_window, self.listViews)
            self.connect(view_window, QtCore.SIGNAL("viewCloses()"),
                         listitem.view_destroyed)
            self.listViews.setCurrentItem(listitem)
            self.listViews.emit(QtCore.SIGNAL("viewsChanged()"))

    def createNewTool(self):
        """Method called when the user selects a new tool to be opened. Creates
           a new instance of the tool and adds a QActiveViewsListWidgetItem to
           the list of open tools (self.listTools).
        """
        tool_window = None
        if self.sender() == self.actionTrajectoryToolLagranto:
            # Trajectory tool.
            tool_window = trajectories_tool.MSSTrajectoriesToolWindow(
                parent=self, listviews=self.listViews)
        elif self.sender() == self.actionDiscoverEarthObservationDataGENESI:
            # GENESI client tool.
            tool_window = genesi_tool.MSSGenesiToolWindow(parent=self)

        if tool_window:
            # Make sure view window will be deleted after being closed, not
            # just hidden (cf. Chapter 5 in PyQt4).
            tool_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            # Open as a non-modal window.
            tool_window.show()
            # Add an entry referencing the new view to the list of views.
            listitem = QActiveViewsListWidgetItem(tool_window, self.listTools)
            self.connect(tool_window, QtCore.SIGNAL("moduleCloses()"),
                         listitem.view_destroyed)

    def activateWindow(self, item):
        """When the user clicks on one of the open view or tool windows, this
           window is brought to the front. This function implements the slot to
           activate a window if the user selects it in the list of views or
           tools.
        """
        # Restore the activated view and bring it to the front.
        item.window.showNormal()
        item.window.raise_()
        item.window.activateWindow()

    new_flight_track_counter = 0

    def createNewFlightTrack(self, template=None,
                             filename=None, activate=False):
        """Creates a new flight track model from a template. Adds a new entry to
           the list of flight tracks. Called when the user selects the 'new/open
           flight track' menu entries.

        Arguments:
        template -- copy the specified template to the new flight track (so that
                    it is not empty).
        filename -- if not None, load the flight track in the specified file.
        activate -- set the new flight track to be the active flight track.
        """

        if template is None:
            template = []
            waypoints = config_loader(dataset="new_flighttrack_template", default=mss_default.new_flighttrack_template)
            for wp in waypoints:
                template.append(ft.Waypoint(flightlevel=0, location=wp))

        if filename:
            waypoints_model = ft.WaypointsTableModel(filename=filename)
        else:
            # Create a new flight track from the waypoints template.
            self.new_flight_track_counter += 1
            waypoints_model = ft.WaypointsTableModel(name="new flight track (%i)" %
                                                          self.new_flight_track_counter)
            # Make a copy of the template. Otherwise all new flight tracks would
            # use the same data structure in memory.
            template_copy = copy.deepcopy(template)
            waypoints_model.insertRows(0, rows=len(template_copy),
                                       waypoints=template_copy)
        # Create a new list entry for the flight track. Make the item name
        # editable.
        listitem = QFlightTrackListWidgetItem(waypoints_model, self.listFlightTracks)
        listitem.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        if activate:
            self.listFlightTracks.setCurrentItem(listitem)
            self.setFlightTrackActive()

    def openConfigFile(self):
        """
        Reads the config file

        Returns:

        """
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     "Open Config file", "",
                                                     "Supported files (*.json *.txt)"
                                                     )
        if not filename.isEmpty():
            constants.CACHED_CONFIG_FILE = str(filename)

    def openFlightTrack(self):
        """Slot for the 'Open Flight Track' menu entry. Opens a QFileDialog and
           passes the result to createNewFlightTrack().
        """
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     "Open Flight Track", "",
                                                     "Flight track XML (*.ftml)")

        if not filename.isEmpty():
            filename = str(filename)
            if filename.endswith('.ftml'):
                self.createNewFlightTrack(filename=filename, activate=True)
            else:
                QtGui.QMessageBox.warning(self, "Open flight track",
                                          "No supported file extension recognized!\n{:}".format(filename),
                                          QtGui.QMessageBox.Ok)

    def closeFlightTrack(self):
        """Slot to close the currently selected flight track. Flight tracks can
           only be closed if at least one other flight track remains open. The
           currently active flight track cannot be closed.
        """
        if self.listFlightTracks.count() < 2:
            QtGui.QMessageBox.information(self, self.tr("Flight Track Management"),
                                          self.tr("At least one flight track has to be open."))
            return
        item = self.listFlightTracks.currentItem()
        if item.flighttrack_model == self.active_flight_track:
            QtGui.QMessageBox.information(self, self.tr("Flight Track Management"),
                                          self.tr("Cannot close currently active flight track."))
            return
        if item.flighttrack_model.modified:
            ret = QtGui.QMessageBox.warning(self, self.tr("Mission Support System"),
                                            self.tr("The flight track you are about to close has "
                                                    "been modified. Close anyway?"),
                                            QtGui.QMessageBox.Yes,
                                            QtGui.QMessageBox.No | QtGui.QMessageBox.Default)
            if ret == QtGui.QMessageBox.Yes:
                self.listFlightTracks.takeItem(self.listFlightTracks.currentRow())

    def saveFlightTrack(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        filename = self.active_flight_track.getFilename()
        if filename:
            sel = QtGui.QMessageBox.question(self, "Save flight track",
                                             "Saving flight track to {:s}. Continue?".format(filename),
                                             QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if sel == QtGui.QMessageBox.Yes:
                if filename.endswith('.ftml'):
                    self.active_flight_track.saveToFTML(filename)
                else:
                    QtGui.QMessageBox.warning(self, "Save flight track",
                                              "Unknown file extension {:s}. Not saving!".format(filename),
                                              QtGui.QMessageBox.Ok)
        else:
            self.saveFlightTrackAs()

    def saveFlightTrackAs(self):
        """Slot for the 'Save Active Flight Track As' menu entry.
        """
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Save Flight Track",
                                                     os.path.join(self.lastSaveDir,
                                                                  self.active_flight_track.name),
                                                     "Flight track XML (*.ftml)"
                                                     )

        if not filename.isEmpty():
            filename = str(filename)
            self.lastSaveDir = os.path.dirname(filename)
            if filename.endswith('.ftml'):
                self.active_flight_track.saveToFTML(filename)
            else:
                QtGui.QMessageBox.warning(self, "Save flight track",
                                          "No supported file extension recognized!\n{:}".format(filename),
                                          QtGui.QMessageBox.Ok)

    def setFlightTrackActive(self):
        """Set the currently selected flight track to be the active one, i.e.
           the one that is displayed in the views (only one flight track can be
           displayed at a time).
        """
        item = self.listFlightTracks.currentItem()
        self.active_flight_track = item.flighttrack_model
        self.lblActiveFlightTrack.setText(item.flighttrack_model.name)
        for i in range(self.listViews.count()):
            view_item = self.listViews.item(i)
            view_item.window.setFlightTrackModel(self.active_flight_track)

    def flightTrackNameChanged(self, item):
        """Slot to react to a name change of the flight tracks in the list
           (i.e. when the user has edited a name). If the changed name
           belongs to the currently active flight track, change its name
           in the label that displays the active track.
        """
        if item.flighttrack_model == self.active_flight_track:
            self.lblActiveFlightTrack.setText(item.text())
        filename = item.flighttrack_model.filename \
            if item.flighttrack_model.filename else ""
        item.setToolTip(filename)

    def showAboutDlg(self):
        """Show the 'About MSUI' dialog to the user.
        """
        dlg = MSS_AboutDialog(parent=self)
        dlg.setModal(True)
        dlg.exec_()


def main():
    print "Launching user interface.."
    app = QtGui.QApplication(sys.argv)
    mainwindow = MSSMainWindow()
    mainwindow.createNewFlightTrack(activate=True)
    mainwindow.show()
    sys.exit(app.exec_())


"""
MAIN PROGRAM
"""

if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    main()
