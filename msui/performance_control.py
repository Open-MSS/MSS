"""Control widget to access the Flight Performance Service. Heavily
   borrows code from "wms_control.py".

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

This file is part of the Mission Support System User Interface (MSUI).

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
from datetime import datetime
import logging
import re
import Queue
import urllib2
import threading

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# local application imports
import ui_performance_dockwidget as ui
import wms_capabilities
import mss_settings
from wms_control import MSSWebMapService
import flighttrack as ft

"""
Settings imported from mss_settings
"""

default_FPS = mss_settings.default_FPS

"""
CLASS PerformanceControlWidget
"""


class PerformanceControlWidget(QtGui.QWidget, ui.Ui_PerformanceDockWidget):
    """The base class of the performance control widget: Provides the GUI
       elements and common functionality to access the flight performance
       service.
    """

    def __init__(self, parent=None, crs_filter="PERF:1",
                 default_FPS=[], model=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        crs_filter -- display only those layers in the 'Modes' combobox
                      whose names match this regexp. Can be used to filter
                      layers. Default is to display all layers.
        default_FPS -- list of strings that specify FPS URLs that will be
                       displayed in the URL combobox as default values.
        """
        super(PerformanceControlWidget, self).__init__(parent)
        self.setupUi(self)

        # Flight track model.
        self.model = model

        # Accomodates MSSWebMapService instances.
        self.wms = None

        # Initial list of WMS servers.
        self.cbURL.clear()
        self.cbURL.addItems(default_FPS)

        # Compile regular expression used in crsAllowed() to filter
        # layers accordings to their CRS.
        self.crs_filter = re.compile(crs_filter)

        # Initially allowed WMS parameters and date/time formats.
        self.init_time_format = "%Y-%m-%dT%H:%M:%SZ"
        self.time_format = "%Y-%m-%dT%H:%M:%SZ"
        self.init_time_name = ""
        self.valid_time_name = ""

        self.layerChangeInProgress = False

        # Initialise GUI elements that control WMS parameters.
        self.cbMode.clear()
        self.cbAircraft.clear()
        self.cbInitTime.clear()

        self.enableInitTimeElements(False)
        self.btComputePerformance.setEnabled(False)
        self.tbViewCapabilities.setEnabled(False)

        # Initialise date/time fields with current day, 00 UTC.
        self.dteTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0,
                                      microsecond=0)))

        # Connect slots and signals.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.connect(self.btGetCapabilities, QtCore.SIGNAL("clicked()"),
                     self.getCapabilities)
        self.connect(self.tbViewCapabilities, QtCore.SIGNAL("clicked()"),
                     self.viewCapabilities)

        self.connect(self.cbMode, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.modeChanged)

        self.connect(self.tbInitTime_cbback, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_back_click)
        self.connect(self.tbInitTime_cbfwd, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_fwd_click)

        self.connect(self.tbMoreOptions, QtCore.SIGNAL("clicked()"),
                     self.switchOptions)
        self.connect(self.tbOptionsBack, QtCore.SIGNAL("clicked()"),
                     self.switchOptions)

        self.connect(self.btComputePerformance, QtCore.SIGNAL("clicked()"),
                     self.getPerformance)

        # Progress dialog to inform the user about image ongoing retrievals.
        self.pdlg = QtGui.QProgressDialog("computing flight performance...", "Cancel",
                                          0, 10, self)

    def getCapabilities(self):
        """Query the server in the URL combobox for its capabilities. Fill
           mode, etc. combo boxes.
        """
        # Clear layer and style combo boxes. First disconnect the modeChanged
        # slot to avoid calls to this function.
        self.disconnect(self.cbMode, QtCore.SIGNAL("currentIndexChanged(int)"),
                        self.modeChanged)
        self.cbMode.clear()
        self.cbAircraft.clear()

        # Load new WMS. Only add those layers to the combobox that can provide
        # the CRS that match the filter of this module.
        base_url = str(self.cbURL.currentText())
        logging.debug("requesting capabilities from %s" % base_url)
        try:
            wms = MSSWebMapService(base_url, version='1.1.1')
        except Exception as ex:
            logging.error("ERROR: %s", ex)
            logging.error("cannot load capabilities document.. "
                          "no layers can be used in this view.")
            QtGui.QMessageBox.critical(self, self.tr("Flight Performance Service"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
            self.wms = None
        else:
            # Parse layer tree of the wms object and discover usable layers.
            stack = wms.contents.values()
            filtered_layers = []
            while len(stack) > 0:
                layer = stack.pop()
                if len(layer.layers) == 0:
                    if self.crsAllowed(layer):
                        # cb_string = "%s | %s" % (layer.name, layer.title)
                        cb_string = "%s | %s" % (layer.title, layer.name)
                        if cb_string not in filtered_layers:
                            filtered_layers.append(cb_string)
                else:
                    stack.extend(layer.layers)
            logging.debug("discovered %i layers that can be used in this view" %
                          len(filtered_layers))
            filtered_layers.sort()
            self.cbMode.addItems(filtered_layers)
            self.wms = wms
            self.modeChanged(0)
            self.btComputePerformance.setEnabled(True)
            self.tbViewCapabilities.setEnabled(True)

        # Reconnect modeChanged.
        self.connect(self.cbMode, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.modeChanged)

    def viewCapabilities(self):
        """Open a WMSCapabilitiesBrowser dialog showing the capabilities
           document.
        """
        logging.debug("Opening capabilities browser..")
        if self.wms is not None:
            wmsbrws = wms_capabilities.WMSCapabilitiesBrowser(
                parent=self,
                url=self.wms.url,
                capabilities_xml=self.wms.capabilities_document)
            wmsbrws.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            wmsbrws.show()

    def crsAllowed(self, layer):
        """Check whether the CRS in which the layer can be provided are allowed
           by the filter that was given to this module (in the constructor).
        """
        if hasattr(layer, "crsOptions") and layer.crsOptions is not None:
            for crs in layer.crsOptions:
                # If one of the CRS supported by the layer matches the filter
                # return True.
                if self.crs_filter.match(crs):
                    return True
        return False

    def interpret_timestring(self, timestring, return_format=False):
        """Tries to interpret a given time string.

        Returns a datetime objects if the method succeeds, otherwise None.
        If return_format=True the method returns the format string for
        datetime.str(f/p)time.
        """
        formats = ["%Y-%m-%dT%H:%M:%SZ",
                   "%Y-%m-%dT%H:%M:%S",
                   "%Y-%m-%dT%H:%M",
                   "%Y-%m-%dT%H:%M:%S.000Z",
                   "%Y-%m-%d"]
        for format in formats:
            try:
                d = datetime.strptime(timestring, format)
                if return_format:
                    return format
                else:
                    return d
            except:
                pass
        return None

    def get_layer_object(self, layername):
        """Returns the object from the layer tree that fits the given
           layer name.
        """
        if layername in self.wms.contents.keys():
            return self.wms.contents[layername]
        else:
            stack = self.wms.contents.values()
            while len(stack) > 0:
                layer = stack.pop()
                if layer.name == layername:
                    return layer
                if len(layer.layers) > 0:
                    stack.extend(layer.layers)
        return None

    def modeChanged(self, index):
        """Slot that updates the <cbAircraft> and <teLayerAbstract> GUI elements
           when the user selects a new layer in <cbMode>.
        """
        layer = self.getMode()
        if not self.wms or layer == '':
            # Do not execute this method if no WMS has been registered or no
            # layer is available (layer will be an empty string then).
            return
        self.layerChangeInProgress = True  # Flag for autoUpdate()
        layerobj = self.get_layer_object(layer)

        self.cbAircraft.clear()
        if "aircraft" in layerobj.dimensions.keys() and "aircraft" in layerobj.extents.keys():
            self.cbAircraft.addItems(["%s" % s for s in layerobj.extents["aircraft"]["values"]])

        abstract_text = layerobj.abstract if layerobj.abstract else ""
        abstract_text = ' '.join([s.strip() for s in abstract_text.splitlines()])
        self.teLayerAbstract.setText(abstract_text)

        # Handle dimensions:
        # ~~~~~~~~~~~~~~~~~~
        save_init_time = self.getInitTime()

        enable_inittime = False
        self.cbInitTime.clear()

        # ~~~~ A) Initialisation time.
        self.init_time_format = None
        if "init_time" in layerobj.dimensions.keys() and "init_time" in layerobj.extents.keys():
            self.init_time_name = "init_time"
            enable_inittime = True

        # Initialisation tag was found: Try to determine the format of
        # the date/time strings and read the provided extent values.
        # Add the extent values to the init time combobox.
        if enable_inittime:
            self.init_time_format = self.interpret_timestring(
                layerobj.extents[self.init_time_name]["values"][0],
                return_format=True)
            self.cbInitTime.addItems(layerobj.extents[self.init_time_name]["values"])
            self.cbInitTime.setCurrentIndex(self.cbInitTime.count() - 1)

        # ~~~~ B) Valid time.
        self.cbTimeOn.setToolTip("")
        font = self.cbTimeOn.font()
        font.setBold(False)
        self.cbTimeOn.setFont(font)
        vtime_no_extent = False
        self.valid_time_format = None
        if "time" in layerobj.dimensions.keys() and "time" in layerobj.extents.keys():
            self.valid_time_name = "time"
            enable_validtime = True
        elif "time" in layerobj.dimensions.keys():
            enable_validtime = True
            self.valid_time_name = "time"
            vtime_no_extent = True

        # Both time dimension and time extent tags were found. Try to determine the
        # format of the date/time strings.
        if enable_validtime and not vtime_no_extent:
            items = layerobj.extents[self.valid_time_name]["values"]
            if len(items) > 0:
                if items[0].find("/") > 0:
                    # A "/" indicates a time range. Do NOT put any
                    # values in the combo box and try to determine the time
                    # format. Times are specified only by the date/time element
                    # in this case.
                    self.valid_time_format = self.interpret_timestring(items[0].split("/")[0],
                                                                       return_format=True)
                    font = self.cbTimeOn.font()
                    font.setBold(True)
                    self.cbTimeOn.setFont(font)
                    self.cbTimeOn.setToolTip(items[0])
                    vtime_no_extent = True
                else:
                    # Determine time format and try to determine allowed times.
                    self.valid_time_format = self.interpret_timestring(items[0],
                                                                       return_format=True)
                    self.cbValidTime.addItems(items)

        if enable_inittime and self.init_time_format is None:
            msg = "cannot determine init time format."
            logging.warning("WARNING: %s" % msg)
            if self.cbInitTime.count() == 0:
                # If no values could be read from the extent tag notify
                # the user.
                QtGui.QMessageBox.critical(self, self.tr("Flight Performance Service"),
                                           self.tr("ERROR: %s" % msg),
                                           QtGui.QMessageBox.Ok)
            self.init_time_format = ""
        logging.debug("determined init time format: %s", self.init_time_format)

        if enable_validtime and self.valid_time_format is None:
            msg = "cannot determine time format, using default."
            logging.warning("WARNING: %s" % msg)
            self.valid_time_format = "%Y-%m-%dT%H:%M:%SZ"
        logging.debug("determined time format: %s", self.valid_time_format)

        self.enableTimeElements(enable_validtime)
        self.enableInitTimeElements(enable_inittime)

        # Try to restore previous time settings.
        if save_init_time is not None:
            index = self.cbInitTime.findText(save_init_time)
            self.cbInitTime.setCurrentIndex(index)

        # ~~~~ C) Weight, accuracy, engine decline tool tips.
        self.trySetExtentTooltip(layerobj, "weight", self.cbWeightOn)
        self.sbAccuracy.setEnabled("accuracy" in layerobj.dimensions.keys())
        self.trySetExtentTooltip(layerobj, "accuracy", self.lblAccuracy)
        self.sbEngineDecline.setEnabled("decline" in layerobj.dimensions.keys())
        self.trySetExtentTooltip(layerobj, "decline", self.lblDecline)

        if "accuracy" in layerobj.dimensions.keys():
            if "default" in layerobj.dimensions["accuracy"].keys():
                self.sbAccuracy.setValue(int(layerobj.dimensions["accuracy"]["default"]))
        if "decline" in layerobj.dimensions.keys():
            if "default" in layerobj.dimensions["decline"].keys():
                self.sbAccuracy.setValue(int(layerobj.dimensions["decline"]["default"]))

        self.layerChangeInProgress = False

    def setElementTooltip(self, element, tooltip):
        """Set a tooltip for an element and set the font of the element bold.
        """
        if isinstance(tooltip, str):
            font = element.font()
            font.setBold(True)
            element.setFont(font)
            element.setToolTip(tooltip)
        else:
            font = element.font()
            font.setBold(False)
            element.setFont(font)
            element.setToolTip("")

    def trySetExtentTooltip(self, layerobj, dim_id, element):
        """If the layer object <layerobj> has an entry for <dim_id> in its
           extents dictionary, set the tooltip of element <element> to
           the extent value.
        """
        if dim_id in layerobj.extents.keys():
            self.setElementTooltip(element,
                                   layerobj.extents[dim_id]["values"][0])
        else:
            self.setElementTooltip(element, None)

    def cb_init_time_back_click(self):
        ci = self.cbInitTime.currentIndex()
        if ci > 0:
            ci = ci - 1
        self.cbInitTime.setCurrentIndex(ci)

    def cb_init_time_fwd_click(self):
        ci = self.cbInitTime.currentIndex()
        if ci < self.cbInitTime.count() - 1:
            ci = ci + 1
        self.cbInitTime.setCurrentIndex(ci)

    def autoUpdate(self):
        """If the auto update check box is checked, let btComputePerformance emit a
           clicked() signal everytime this method is called.
           autoUpdate() should be called from the slots that handle
           time and level changes.

        If the the layerChangeInProgress flag is set no update will be
        performed (lock mechanism to prevent erroneous requests during
        a layer change).
        """
        if self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
            self.btComputePerformance.emit(QtCore.SIGNAL("clicked()"))

    def enableInitTimeElements(self, enable):
        """Enables or disables the GUI elements allowing initialisation time
           control.
        """
        self.cbInitialisationOn.setChecked(enable)
        self.cbInitTime.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)
        self.rbNWPinterpolation.setEnabled(enable)
        self.rbNWPnointerpolation.setEnabled(enable)
        self.lblInterpolation.setEnabled(enable)

    def enableTimeElements(self, enable):
        """Enables or disables the GUI elements allowing time control.
        """
        self.cbTimeOn.setChecked(enable)
        self.dteTime.setEnabled(enable)
        self.sbWaypoint.setEnabled(enable)

    def getMode(self):
        return unicode(self.cbMode.currentText(), errors="ignore").split(" | ")[-1]

    def getAircraft(self):
        return unicode(self.cbAircraft.currentText(), errors="ignore").split(" |")[0]

    def getInitTime(self):
        """Get the initialisation time from the GUI elements.

        If the init time date/time edit is enabled (i.e. the times specifed
        in the WMS capabilities document can be interpreted), return a
        datetime object of the currently set time. Otherwise, return the
        string that is selected in the init time combobox.
        """
        if self.cbInitialisationOn.isChecked():
            itime_str = str(self.cbInitTime.currentText())
            return itime_str
        else:
            return None

    def getTime(self):
        """The same as getInitTime(), but for the waypoint time.
        """
        if self.cbTimeOn.isChecked():
            return self.dteTime.dateTime().toPyDateTime()
        else:
            return None

    def switchOptions(self):
        """
        """
        index = self.stackedWidget.currentIndex()
        self.stackedWidget.setCurrentIndex(0 if index else 1)

    def _queued_get_performance(self, queue=None, url=""):
        """Helper routine to retrieve a performance computation result from a
           thread: The return value is stored in the Queue.Queue() object that
           is passed to this routine, to be able to retrieve it after the thread
           has finished its execution.

        See:
          http://stackoverflow.com/questions/1886090/return-value-from-thread
        """
        try:
            urlobject = urllib2.urlopen(url)
            if queue is not None:
                queue.put(urlobject)
        except Exception as e:
            if queue is not None:
                queue.put(e)

    def retrievePerformanceComputation(self):
        """Queries the flight performance service for a flight performance
           computation.
        """

        # Show the progress dialog, (a) since the retrieval can take a few
        # seconds, and (b) to allow for cancellation of the request by the
        # user.
        self.pdlg.setValue(0)
        self.pdlg.setModal(True)
        self.pdlg.reset()
        self.pdlg.show()
        QtGui.QApplication.processEvents()

        # Stores the computation results to be returned (multiline string).
        performance = None

        # Get mode and aircraft names.
        mode = self.getMode()
        aircraft = self.getAircraft()

        # Get time and the waypoint for which it has been specified.
        waypoint_no = self.sbWaypoint.value()
        time = self.getTime()  # datetime object

        # Weight, either takeoff weight or landing weight, depending on the mode.
        weight = self.sbWeight.value()

        # If applicable, get init time values.
        init_time = self.getInitTime()  # string from combobox; None if disabled
        interpolateNWP = self.rbNWPinterpolation.isChecked()

        accuracy_points = self.sbAccuracy.value()
        engine_decline = self.sbEngineDecline.value()

        # Assemble URL.
        url = str(self.cbURL.currentText()) + "?"
        url += "REQUEST=GetPerformance"
        url += "&MODE=" + mode
        url += "&AIRCRAFT=" + aircraft
        url += "&TIME=" + time.strftime(self.time_format)
        url += "&TIME_WP_NO=%i" % waypoint_no
        url += "&WEIGHT=%i" % weight
        url += "&ACCURACY=%i" % accuracy_points
        url += "&DECLINE=%i" % engine_decline

        if init_time is not None:
            url += "&INIT_TIME=" + init_time
            url += "&INTERPOLATION=" + ("1" if interpolateNWP else "0")

        # Coordinates of the flight track.
        waypoints_string = ""
        for waypoint in self.model.allWaypointData(mode=ft.USER):
            waypoints_string += "%f,%f,%f,LRC," % (waypoint.lon, waypoint.lat,
                                                   waypoint.flightlevel)
        waypoints_string = waypoints_string[:-1]
        url += "&COORDINATES=" + waypoints_string

        logging.debug("querying performance service with URL %s" % url)

        try:
            # Start a retrieval thread.
            queue = Queue.Queue()
            kwargs = {"queue": queue, "url": url}
            thread = threading.Thread(target=self._queued_get_performance, kwargs=kwargs)
            thread.start()

            self.pdlg.setValue(1)
            QtGui.QApplication.processEvents()

            while thread.isAlive():
                # This loop keeps the GUI alive while the thread is executing,
                # and checks for a cancellation request by the user.
                QtGui.QApplication.processEvents()
                if self.pdlg.wasCanceled():
                    logging.debug("performance computation was canceled by the user.")
                    raise UserWarning("performance computation was canceled by the user.")
                # Wait for 10 ms if the thread is still running to prevent
                # the application from using 100% processor time.
                thread.join(0.01)

            # See retrieveImage() in wms_control.py..
            if not queue.empty():
                qreturn = queue.get()
                if hasattr(qreturn, "read"):
                    urlobject = qreturn
                else:
                    raise qreturn

            self.pdlg.setValue(8)
            QtGui.QApplication.processEvents()

            # Read the result from the URL into a string (urlobject.read())
            performance = urlobject.read()
            logging.debug("performance result retrieved, size is %i bytes." % len(performance))

        except Exception as ex:
            logging.error("ERROR: %s", ex)
            QtGui.QMessageBox.critical(self, self.tr("Flight Performace Service"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
            # self.pdlg.close()
            # raise ex

        # Close the progress dialog and return the result.
        self.pdlg.close()

        return performance

    def getPerformance(self):
        """Slot for the 'get performance' button.
        """
        logging.error("querying flight performance service..")
        performance = self.retrievePerformanceComputation()
        logging.debug("performance service returned:\n\n%s\n" % performance)
        if performance is not None:
            self.model.setPerformanceComputation(performance)


if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    # Create an example flight track.
    initial_waypoints = [ft.Waypoint(flightlevel=0, location="EDMO", comments="take off OP"),
                         ft.Waypoint(48.10, 10.27, 200),
                         ft.Waypoint(52.32, 09.21, 200),
                         ft.Waypoint(52.55, 09.99, 200),
                         ft.Waypoint(flightlevel=0, location="Hamburg", comments="landing HH")]

    waypoints_model = ft.WaypointsTableModel(QtCore.QString(""))
    waypoints_model.insertRows(0, rows=len(initial_waypoints),
                               waypoints=initial_waypoints)

    import sys

    app = QtGui.QApplication(sys.argv)
    win = PerformanceControlWidget(default_FPS=default_FPS,
                                   model=waypoints_model)
    win.show()
    sys.exit(app.exec_())






# IPYTHON TEST LINES.

# import wms_control; base_url = "http://localhost:8081/mss_wms"; wms = wms_control.MSSWebMapService(base_url, version='1.1.1')
# l = wms.contents["PLGeopWind"]
