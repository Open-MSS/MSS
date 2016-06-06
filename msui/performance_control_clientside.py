"""Control widget to access the Flight Performance Service. Heavily
   borrows code from "wms_control.py".

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

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

TODO:
=====

* make cruise mode customizable (2012Nov13, mr)

"""

# standard library imports
from datetime import datetime
import logging
import re
import threading
import Queue
import hashlib
import os
import time
import xml.dom.minidom

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings
import owslib.util
import numpy as np

# local application imports
import ui_performance_widget_clientside as ui
import wms_capabilities
import mss_settings
from wms_control import MSSWebMapService, MSS_WMS_AuthenticationDialog
import flighttrack as ft
from mslib import performance

"""
Settings imported from mss_settings
"""

wms_cache = mss_settings.wms_cache
num_interpolation_points = mss_settings.num_interpolation_points

"""
CLASS PerformanceControlWidget
"""


class PerformanceControlWidget(QtGui.QWidget, ui.Ui_PerformanceWidget):
    """The base class of the performance control widget: Provides the GUI
       elements and common functionality to access the flight performance
       service.
    """

    def __init__(self, parent=None, crs_filter="VERT:LOGP",
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
        self.available_valid_times = []

        self.layerChangeInProgress = False

        # Initialise GUI elements that control WMS parameters.
        self.cbAircraftConfig.clear()
        self.cbAircraft.clear()
        self.cbAircraft.addItems(performance.available_aircraft.keys())
        if len(performance.available_aircraft.keys()) > 0:
            self.cbAircraft.setCurrentIndex(0)
            self.aircraftChanged(0)
        self.cbWMSLayer.clear()
        self.cbInitTime.clear()

        self.enableNWPElements(False)
        self.btComputePerformance.setEnabled(True)

        # Initialise date/time fields with current day, 00 UTC.
        self.dteTakeoffTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=12, minute=0, second=0,
                                      microsecond=0)))

        # Check for WMS image cache directory, create if neceassary.
        if wms_cache is not None:
            self.wms_cache = os.path.join(wms_cache, "performance")
            logging.debug("checking for WMS image cache at %s ..." % self.wms_cache)
            if not os.path.exists(self.wms_cache):
                logging.debug("  created new image cache directory.")
                os.makedirs(self.wms_cache)
            else:
                logging.debug("  found.")
            # Service the cache (delete files that are too old, remove oldest
            # files if cache is too large).
            self.serviceCache()
        else:
            self.wms_cache = None

        # Connect slots and signals.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.connect(self.btConnectNWP, QtCore.SIGNAL("clicked()"),
                     self.getCapabilities)

        self.connect(self.cbAircraft, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.aircraftChanged)

        self.connect(self.tbInitTime_cbback, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_back_click)
        self.connect(self.tbInitTime_cbfwd, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_fwd_click)

        self.connect(self.btComputePerformance, QtCore.SIGNAL("clicked()"),
                     self.getPerformance)
        self.connect(self.btExportToFX, QtCore.SIGNAL("clicked()"),
                     self.exportToFX)

        self.connect(self.cbUseNWP, QtCore.SIGNAL("toggled(bool)"),
                     self.enableNWPElements)

        self.connect(self.btClearCache, QtCore.SIGNAL("clicked()"),
                     self.clearCache)

        # Progress dialog to inform the user about image ongoing retrievals.
        self.pdlg = QtGui.QProgressDialog("retrieving forecast data..", "Cancel",
                                          0, 10, self)

    def initialiseWMS(self, base_url):
        """Initialises a MSSWebMapService object with the specified base_url.

        If the web server returns a '401 Unauthorized', prompt the user for
        username and password.

        NOTE: owslib (from which MSSWebMapService is derived) only supports
        the basic HTTP authentication. You might hence have to dig deeper into
        the code for more sophisticated authentication methods.

        See: 1) http://pythonpaste.org/modules/auth.basic.html#module-paste.auth.basic
             2) method 'openURL' in owslib.util

        (mr, 2011-02-25)
        """
        wms = None
        username = None
        password = None
        try:
            while wms is None:
                try:
                    wms = MSSWebMapService(base_url, version='1.1.1',
                                           username=username, password=password)
                except owslib.util.ServiceException as ex:
                    if str(ex).startswith("401"):
                        # Catch the "401 Unauthorized" error if one has been
                        # returned by the server and ask the user for username
                        # and password.
                        dlg = MSS_WMS_AuthenticationDialog(parent=self)
                        dlg.setModal(True)
                        if dlg.exec_() == QtGui.QDialog.Accepted:
                            username, password = dlg.getAuthInfo()
                        else:
                            break
                    else:
                        raise ex
        except Exception as ex:
            logging.error("ERROR: %s", ex)
            logging.error("cannot load capabilities document.. "
                          "no layers can be used in this view.")
            QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
        return wms

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

    def getCapabilities(self):
        """Query the WMS server in the URL combobox for its capabilities. Fill
           layer, style, etc. combo boxes.
        """
        # Clear layer combo box. First disconnect the layerChanged slot to avoid
        # calls to this function.
        self.disconnect(self.cbWMSLayer, QtCore.SIGNAL("currentIndexChanged(int)"),
                        self.layerChanged)
        self.cbWMSLayer.clear()
        self.cbInitTime.clear()
        self.available_valid_times = []

        # Load new WMS. Only add those layers to the combobox that can provide
        # the CRS that match the filter of this module.
        base_url = str(self.cbURL.currentText())
        logging.debug("requesting capabilities from %s" % base_url)
        wms = self.initialiseWMS(base_url)
        if wms is not None:
            # Parse layer tree of the wms object and discover usable layers.
            stack = wms.contents.values()
            filtered_layers = []
            while len(stack) > 0:
                layer = stack.pop()
                if len(layer.layers) == 0:
                    if self.crsAllowed(layer):
                        if layer.name.endswith("VS_HV01"):
                            # TODO: We only want data from the horizontal wind section. However, hard-coding
                            # the layer name here isn't a good solution; find a better one.. (mr, 2012Nov09)
                            cb_string = "%s | %s" % (layer.title, layer.name)
                            # cb_string = layer.name.split(".")[0]
                            if cb_string not in filtered_layers:
                                filtered_layers.append(cb_string)
                else:
                    stack.extend(layer.layers)
            logging.debug("discovered %i layers that can be used in this view" %
                          len(filtered_layers))
            filtered_layers.sort()
            self.cbWMSLayer.addItems(filtered_layers)
            self.wms = wms
            self.layerChanged(0)

        # Reconnect layerChanged.
        self.connect(self.cbWMSLayer, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.layerChanged)

    def getWMSLayer(self):
        return unicode(self.cbWMSLayer.currentText(), errors="ignore").split(" | ")[-1]

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

    def layerChanged(self, index):
        """This slot is called when the user changes the WMS layer that is used
        to retrieve the forecast data. It updates the list of init times
        displayed to the user. Also, a list of available valid (=forecast) times
        is created.
        """
        layer = self.getWMSLayer()
        if not self.wms or layer == '':
            # Do not execute this method if no WMS has been registered or no
            # layer is available (layer will be an empty string then).
            return

        # Clear old list of init times.
        self.cbInitTime.clear()

        # Traverse the XML tree of the WMS capabilities document, starting at
        # the current layer node, going up until init time information are
        # found.
        layerobj = self.get_layer_object(layer)
        lobj = layerobj
        while lobj is not None:
            if "init_time" in lobj.dimensions.keys() \
                    and "init_time" in lobj.extents.keys():
                items = [i.strip() for i in lobj.extents["init_time"]["values"]]
                if len(items) > 0:
                    # Determine time format and determine available
                    # times. Convert the list into a sorted numpy array that can
                    # be searched with the searchsorted() function.
                    self.init_time_format = self.interpret_timestring(
                        items[0], return_format=True)
                    self.cbInitTime.addItems(items)
                    break

            # One step up in the level hierarchy: If no dimension values
            # were identified, check if this layer inherits some from its
            # parent.
            lobj = lobj.parent

        # Traverse again to find valid time information.
        self.available_valid_times = []
        lobj = layerobj
        while lobj is not None:
            if "time" in lobj.dimensions.keys() \
                    and "time" in lobj.extents.keys():
                items = [i.strip() for i in lobj.extents["time"]["values"]]
                if len(items) > 0:
                    # Determine time format and determine available
                    # times. Convert the list into a sorted numpy array that can
                    # be searched with the searchsorted() function.
                    self.valid_time_format = self.interpret_timestring(
                        items[0], return_format=True)
                    self.available_valid_times = [
                        datetime.strptime(val, self.valid_time_format) for val in items]
                    self.available_valid_times = np.array(self.available_valid_times)
                    self.available_valid_times.sort()
                    break

            # One step up in the level hierarchy: If no dimension values
            # were identified, check if this layer inherits some from its
            # parent.
            lobj = lobj.parent

    def aircraftChanged(self, index):
        """Slot that updates the <cbAircraftConfig> GUI element as well as
           weight limits when the user selects an aircraft in <cbAircraft>.
        """
        aircraftName = str(self.cbAircraft.currentText())  # convert from QString
        if aircraftName == '':
            return

        aircraft = performance.available_aircraft[aircraftName]

        self.cbAircraftConfig.clear()
        self.cbAircraftConfig.addItems(aircraft.availableConfigurations)

        self.sbTakeoffWeight.setMinimum(aircraft.maximumTakeoffWeight_lbs - aircraft.fuelCapacity_lbs)
        self.sbTakeoffWeight.setMaximum(aircraft.maximumTakeoffWeight_lbs)
        self.sbTakeoffWeight.setValue(aircraft.maximumTakeoffWeight_lbs)

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

    def enableNWPElements(self, enable):
        """Enables or disables the GUI elements that connect to a NWP web
        service.
        """
        self.cbUseNWP.setChecked(enable)
        self.cbURL.setEnabled(enable)
        self.btConnectNWP.setEnabled(enable)
        self.cbWMSLayer.setEnabled(enable)
        self.cbInitTime.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)
        self.lblNWPWarning.setEnabled(enable)

    def getInitTime(self):
        """Get the initialisation time from the GUI elements.
        """
        return str(self.cbInitTime.currentText())

    def _queued_get_map(self, queue=None, **kwargs):
        """Helper routine to call getmap() from a thread: The return value
           is stored in the Queue.Queue() object that is passed to this routine,
           to be able to retrieve it after the thread has finished its
           execution.

        See:
          http://stackoverflow.com/questions/1886090/return-value-from-thread
        """
        try:
            urlobject = self.wms.getmap(**kwargs)
            if queue is not None:
                queue.put(urlobject)
        except Exception as e:
            if queue is not None:
                queue.put(e)

    def cachingEnabled(self):
        """Returns if the image cache is enabled.
        """
        return self.wms_cache is not None and self.cbCacheEnabled.isChecked()

    def retrieveForecast(self, layer=None, init_time=None, valid_time_list=[],
                         bbox=None, path_string=None):
        """
        Arguments:
        crs -- coordinate reference system as a string passed to the WMS
        path_string -- string of waypoints that resemble a vertical
                       section path. Can be omitted for horizontal
                       sections.
        bbox -- bounding box as list of four floats

        Returns..
        """

        # Show the progress dialog, (a) since the retrieval can take a few
        # seconds, and (b) to allow for cancellation of the request by the
        # user.
        self.pdlg.setValue(0)
        self.pdlg.setModal(True)
        self.pdlg.reset()
        self.pdlg.show()
        QtGui.QApplication.processEvents()
        self.pdlg.setValue(0.1)
        QtGui.QApplication.processEvents()

        data = []

        for iv, valid_time in enumerate(valid_time_list):

            # Stores the data to be returned in xml format. If an error occurs, None
            # will be returned.
            xml = None

            logging.debug("fetching forecast data from WMS layer %s", layer)
            logging.debug("init_time=%s, valid_time=%s" % (init_time, valid_time))

            try:
                # Call the self.wms.getmap() method in a separate thread to keep
                # the GUI responsive.
                # NOTES:
                # a) This can be done with either a QThread (seems to require
                #    subclassing), or a Python thread (the way I did here).
                #    See: http://stackoverflow.com/questions/1595649/
                #                threading-in-a-pyqt-application-use-qt-threads-or-python-threads
                # b) To retrieve the return value of getmap, a Queue is used.
                #    See: http://stackoverflow.com/questions/1886090/return-value-from-thread
                kwargs = {"layers": [layer],
                          "styles": [""],
                          "srs": "VERT:LOGP",
                          "bbox": bbox,
                          "path_str": path_string,
                          "time": valid_time,
                          "init_time": init_time,
                          "level": None,
                          "time_format": self.valid_time_format,
                          "init_time_format": self.init_time_format,
                          "time_name": "time",
                          "init_time_name": "init_time",
                          "size": (100, 100),
                          "format": 'text/xml',
                          "transparent": False}

                # If caching is enabled, get the URL and check the cache directory
                # for the suitable file.
                cache_hit = False
                if self.cachingEnabled():
                    kwargs["return_only_url"] = True
                    urlstr = self.wms.getmap(**kwargs)
                    kwargs["return_only_url"] = False
                    # Get an md5 digest of the URL string. The digest is used
                    # as the filename.
                    md5_filename = hashlib.md5(urlstr).hexdigest()
                    md5_filename += ".xml"
                    logging.debug("checking cache for image file %s ..." %
                                  md5_filename)
                    md5_filename = os.path.join(self.wms_cache, md5_filename)
                    if os.path.exists(md5_filename):
                        logging.debug("  file exists, loading from cache.")
                        cache_hit = True
                    else:
                        logging.debug("  file does not exist, retrieving from WMS server.")

                if not cache_hit:

                    queue = Queue.Queue()
                    kwargs["queue"] = queue
                    thread = threading.Thread(target=self._queued_get_map, kwargs=kwargs)
                    thread.start()

                    while thread.isAlive():
                        # This loop keeps the GUI alive while the thread is executing,
                        # and checks for a cancellation request by the user.
                        QtGui.QApplication.processEvents()
                        if self.pdlg.wasCanceled():
                            logging.debug("map retrieval was canceled by the user.")
                            raise UserWarning("map retrieval was canceled by the user.")
                        # Wait for 10 ms if the thread is still running to prevent
                        # the application from using 100% processor time.
                        thread.join(0.01)

                    # Get the return value from getmap() from the queue. If everything
                    # went well, the return value is a urlobject instance, otherwise
                    # it is an Exception.
                    # NOTE: I can't figure out how to distinguish between the Exception
                    # types and the urlobject. "type(qreturn) is Exception" doesn't
                    # work, I'd have to list all possible exception types.
                    # "type(urlobject)" returns "instance", which doesn't help much
                    # either. Hence I merely test for a read() method.
                    if not queue.empty():
                        qreturn = queue.get()
                        if hasattr(qreturn, "read"):
                            urlobject = qreturn
                        else:
                            raise qreturn

                    self.pdlg.setValue(10. * (iv + 1) / len(valid_time_list))
                    QtGui.QApplication.processEvents()
                    # Read the image file from the URL into a string (urlobject.read()).
                    xml = urlobject.read()
                    logging.debug("data layer retrieved")
                    # Store the retrieved image in the cache, if enabled.
                    if self.cachingEnabled():
                        logging.debug("storing retrieved xml file in cache.")
                        xmlfile = open(md5_filename, "w")
                        xmlfile.write(xml)
                        xmlfile.close()
                else:
                    xmlfile = open(md5_filename)
                    xml = xmlfile.read()
                    xmlfile.close()
                    logging.debug("layer retrieved from cache.")

            except Exception as ex:
                self.pdlg.close()
                logging.error("ERROR: %s", ex)
                QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                           self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                           QtGui.QMessageBox.Ok)
                raise ex

            data.append(xml)

        # Close the progress dialog and return the image.
        self.pdlg.close()

        return data

    def clearCache(self):
        """Clear the image file cache. First ask the user for confirmation.
        """
        # User confirmation to clear the cache.
        clear = (QtGui.QMessageBox.question(
            self, "Clear Cache",
            "Do you really want to clear the cache? All stored image "
            "files will be deleted.",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes)
        if clear:
            # Delete all files in cache.
            if self.wms_cache is not None:
                cached_files = os.listdir(self.wms_cache)
                logging.debug("clearing cache; deleting %i files.."
                              % len(cached_files))
                for f in cached_files:
                    try:
                        os.remove(os.path.join(self.wms_cache, f))
                    except Exception as e:
                        logging.error("ERROR: %s" % e)
                logging.debug("cache has been cleared.")
            else:
                logging.debug("no cache exists that can be cleared.")

    def serviceCache(self):
        """Service the cache: Remove all files older than the maximum file
           age specified in mss_settings, and remove the oldest files if the
           maximum cache size has been reached.
        """
        logging.debug("servicing cache..")

        # Create a list of all files in the cache.
        files = [os.path.join(self.wms_cache, f)
                 for f in os.listdir(self.wms_cache)]
        # Add the ages of the files (via modification times in sec since epoch)
        # and the file sizes.
        # (current time in sec since epoch)
        current_time = time.time()
        files = [(f, os.path.getsize(f), current_time - os.path.getmtime(f))
                 for f in files if os.path.isfile(f)]
        # Sort the files accordings to their age (i.e. use the
        # third argument of the tuples (file, fsize, fage) as the sorting key).
        files.sort(key=lambda x: x[2])

        # Loop over all cached files, staring with the youngest. Once the
        # maximum cache size has been reached, all files left will be
        # removed (i.e. the oldest files). All files exceeding the maximum
        # file age will also be removed.
        cum_size_bytes = 0
        removed_files = 0
        for f, fsize, fage in files:
            cum_size_bytes += fsize
            if (cum_size_bytes > mss_settings.wms_cache_max_size_bytes) or fage > mss_settings.wms_cache_max_age_seconds:
                os.remove(f)
                removed_files += 1

        logging.debug("cache has been cleaned (%i files removed)." % removed_files)

    def parseXMLData(self, xml_data):
        """Parse XMl data retrieved from the WMS Server and convert the
        contained data into numpy arrays. A dictionary is returned with a main
        entry for each timestep in the xml_data.
        """
        data = {}

        # http://docs.python.org/2/library/xml.dom.minidom.html
        def getText(nodelist):
            rc = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data.strip())
            return ''.join(rc)

        for xml_document in xml_data:

            dom = xml.dom.minidom.parseString(xml_document)

            valid_time = dom.getElementsByTagName("ValidTime")[0]
            valid_time = getText(valid_time.childNodes).strip()
            valid_time = datetime.strptime(valid_time, self.valid_time_format)

            data[valid_time] = {}

            lons = dom.getElementsByTagName("Longitude")[0]
            lons = getText(lons.childNodes).strip()
            data[valid_time]["lon"] = np.array([float(f) for f in lons.split(",")])

            lats = dom.getElementsByTagName("Latitude")[0]
            lats = getText(lats.childNodes).strip()
            data[valid_time]["lat"] = np.array([float(f) for f in lats.split(",")])

            data_node = dom.getElementsByTagName("Data")[0]

            air_pressure = data_node.getElementsByTagName("air_pressure")
            if len(air_pressure) == 0:
                raise ValueError("cannot find air_pressure in data file")
            air_pressure = getText(air_pressure[0].childNodes)
            air_pressure = air_pressure.split("\n")
            air_pressure = np.array([[float(f) for f in line.split(",")]
                                     for line in air_pressure])
            data[valid_time]["air_pressure"] = air_pressure

            eastward_wind = data_node.getElementsByTagName("eastward_wind")
            if len(eastward_wind) == 0:
                raise ValueError("cannot find eastward_wind in data file")
            eastward_wind = getText(eastward_wind[0].childNodes)
            eastward_wind = eastward_wind.split("\n")
            eastward_wind = np.array([[float(f) for f in line.split(",")]
                                      for line in eastward_wind])
            data[valid_time]["eastward_wind"] = eastward_wind

            northward_wind = data_node.getElementsByTagName("northward_wind")
            if len(northward_wind) == 0:
                raise ValueError("cannot find northward_wind in data file")
            northward_wind = getText(northward_wind[0].childNodes)
            northward_wind = northward_wind.split("\n")
            northward_wind = np.array([[float(f) for f in line.split(",")]
                                       for line in northward_wind])
            data[valid_time]["northward_wind"] = northward_wind

            air_temperature = data_node.getElementsByTagName("air_temperature")
            if len(air_temperature) == 0:
                raise ValueError("cannot find air_temperature in data file")
            air_temperature = getText(air_temperature[0].childNodes)
            air_temperature = air_temperature.split("\n")
            air_temperature = np.array([[float(f) for f in line.split(",")]
                                        for line in air_temperature])
            data[valid_time]["air_temperature"] = air_temperature

        return data

    def getPerformance(self):
        """Slot for the 'compute performance' button.
        """
        logging.debug("computing flight performance..")

        aircraft_name = str(self.cbAircraft.currentText())  # convert from QString
        if aircraft_name == '':
            return
        aircraft_config = str(self.cbAircraftConfig.currentText())
        if aircraft_config == '':
            return

        # Get the aircraft object.
        aircraft = performance.available_aircraft[aircraft_name]
        aircraft.selectConfiguration(aircraft_config)
        aircraft.setPerformanceTableInterpretation("interpolation")
        aircraft.setErrorHandling("strict")

        takeoff_time = self.dteTakeoffTime.dateTime().toPyDateTime()
        takeoff_weight = self.sbTakeoffWeight.value()

        logging.debug("aircraft: %s (%s)" % (aircraft_name, aircraft_config))
        logging.debug("takeoff at %s with weight %i lbs" %
                      (takeoff_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       takeoff_weight))

        # Setup an initial flight track description for the performance module.
        flight_description = [
            ["takeoff_weight", takeoff_weight],
            ["takeoff_time", takeoff_time.strftime("%Y-%m-%dT%H:%M:%SZ")],
            ["temperature_ISA_deviation", 0]
        ]

        # Insert waypoints of the current flight track.
        waypoints = self.model.allWaypointData(mode=ft.USER)
        if len(waypoints) < 3:
            logging.error("for performance computations, the flight track "
                          "must consist of at least three waypoints.")
            return

        # The first two waypoints describe start and climb.
        flight_description.append(["takeoff_location",
                                   waypoints[0].lon, waypoints[0].lat])
        flight_description.append(["climb_descent_to",
                                   waypoints[1].lon, waypoints[1].lat,
                                   waypoints[1].flightlevel * 100])

        prev_waypoint = waypoints[1]
        for waypoint in waypoints[2:-1]:
            if waypoint.flightlevel != prev_waypoint.flightlevel:
                flight_description.append(["climb_descent_to",
                                           waypoint.lon, waypoint.lat,
                                           waypoint.flightlevel * 100])
            else:
                # TODO: Make cruise mode customizable.
                flight_description.append(["cruise_to",
                                           waypoint.lon, waypoint.lat,
                                           aircraft.defaultCruiseMode])
            prev_waypoint = waypoint

        # Last waypoint: Target airport.
        flight_description.append(["land_at",
                                   waypoints[-1].lon, waypoints[-1].lat])

        # print flight_description

        # Compute the performance.
        # ====================================================

        logging.debug("calling flight performance module:\n")
        error_occurred = False
        try:
            aircraft.fly(flight_description)
        except Exception as ex:
            logging.error("ERROR: %s", ex)
            logging.error("cannot compute performance of the given flight track.")
            QtGui.QMessageBox.critical(
                self, self.tr("Flight Performance"),
                self.tr("ERROR:\n\n%s\n\n(DEBUG: %s)" % (ex, type(ex))),
                QtGui.QMessageBox.Ok)
            error_occurred = True
        logging.debug("flight performance module has returned.")
        aircraft_statelist_without_nwp = aircraft.getLastAircraftStateList()

        # Should NWP data be considered?
        # ==============================

        if self.cbUseNWP.isChecked() and len(aircraft_statelist_without_nwp) > 0 \
                and not error_occurred:

            if len(self.available_valid_times) == 0:
                msg = "There are no valid forecast timesteps that can be " \
                      "used for the performance computation."
                logging.error("ERROR: %s", msg)
                QtGui.QMessageBox.critical(self, self.tr("Flight Performance"),
                                           self.tr("ERROR:\n\n%s" % msg),
                                           QtGui.QMessageBox.Ok)
                return

            if self.available_valid_times[0] > takeoff_time:
                msg = "The takeoff time %s is earlier than the first available " \
                      "forecast timestep (which is at %s). Please choose a " \
                      "later takeoff time." % \
                      (takeoff_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       self.available_valid_times[0].strftime("%Y-%m-%dT%H:%M:%SZ"))
                logging.error("ERROR: %s", msg)
                QtGui.QMessageBox.critical(self, self.tr("Flight Performance"),
                                           self.tr("ERROR:\n\n%s" % msg),
                                           QtGui.QMessageBox.Ok)
                return

                # Valid layer and init time?
            wms_layer = self.getWMSLayer()
            init_time = self.getInitTime()

            # Determine the valid times before takeoff, after landing and in
            # between those two.
            index_before_takeoff_time = \
                self.available_valid_times.searchsorted(takeoff_time)

            if index_before_takeoff_time >= len(self.available_valid_times):
                msg = "The takeoff time %s is later than the last available " \
                      "forecast timestep (which is at %s). Please choose an " \
                      "earlier takeoff time." % \
                      (takeoff_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       self.available_valid_times[-1].strftime("%Y-%m-%dT%H:%M:%SZ"))
                logging.error("ERROR: %s", msg)
                QtGui.QMessageBox.critical(self, self.tr("Flight Performance"),
                                           self.tr("ERROR:\n\n%s" % msg),
                                           QtGui.QMessageBox.Ok)
                return

            if self.available_valid_times[index_before_takeoff_time] > takeoff_time:
                index_before_takeoff_time = max(index_before_takeoff_time - 1, 0)

            landing_time = aircraft_statelist_without_nwp[-1].time_utc
            index_after_landing_time = \
                self.available_valid_times.searchsorted(landing_time)

            if index_after_landing_time >= len(self.available_valid_times):
                msg = "The landing time %s is later than the last available " \
                      "forecast timestep (which is at %s). Please choose an " \
                      "earlier takeoff time." % \
                      (landing_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       self.available_valid_times[-1].strftime("%Y-%m-%dT%H:%M:%SZ"))
                logging.error("ERROR: %s", msg)
                QtGui.QMessageBox.critical(self, self.tr("Flight Performance"),
                                           self.tr("ERROR:\n\n%s" % msg),
                                           QtGui.QMessageBox.Ok)
                return

            valid_time_list = self.available_valid_times[index_before_takeoff_time:index_after_landing_time + 1]

            print index_before_takeoff_time, self.available_valid_times[index_before_takeoff_time]
            print index_after_landing_time, self.available_valid_times[index_after_landing_time]

            # Get lat/lon coordinates of flight track and convert to string for URL.
            path_string = ""
            for waypoint in self.model.allWaypointData():
                # path_string += "%.2f,%.2f," % (waypoint.lat, waypoint.lon)
                path_string += "%s,%s," % (waypoint.lat, waypoint.lon)
            path_string = path_string[:-1]

            # Request all required time steps. Interpret XML and store forecast
            # data in numpy arrays.
            xml_data = self.retrieveForecast(layer=wms_layer,
                                             init_time=init_time,
                                             valid_time_list=valid_time_list,
                                             bbox=(num_interpolation_points, 1000, 10, 100),
                                             path_string=path_string)

            data = self.parseXMLData(xml_data)

            # Compute the performance with NWP data.
            # ====================================================

            logging.debug("calling flight performance module with NWP data:\n")
            try:
                aircraft.fly(flight_description, nwp_data=data)
            except Exception as ex:
                logging.error("ERROR: %s", ex)
                logging.error("cannot compute performance of the given flight track.")
                QtGui.QMessageBox.critical(
                    self, self.tr("Flight Performance"),
                    self.tr("ERROR:\n\n%s\n\n(DEBUG: %s)" % (ex, type(ex))),
                    QtGui.QMessageBox.Ok)
            logging.debug("flight performance module has returned.")
            aircraft_statelist_with_nwp = aircraft.getLastAircraftStateList()

            self.model.setAircraftStateList(aircraft_statelist_with_nwp)

        else:
            self.model.setAircraftStateList(aircraft_statelist_without_nwp)

    def exportToFX(self):
        """Slot for the 'exportToFX' button. Writes the flight profile to
        a CSV file that can be read with JW's HALO performance
        program developed in his Master's thesis at DLR-FX.

        Output format:

        General Input
        ZeroFuelWeight [Lbs]; Takeoff FuelWeight [Lbs]; ReserveFuel [Lbs]; \
            Flight Distance [NM]; TakeoffAltitude [ft]; Landing Altitude [ft]
        HALO Configuration
        nBellyPod; nWingPod; nPMS; nLIFOH; nTGI; nHAI; nDUALER; nHASI; \
            nCVI; nMAI; nSPARM; nDC; <-- Anzahl der jeweiligen Anbauten
        Flight Legs
        Type; FL; Ma/CAS [Ma oder Kxxx fuer Knoten CAS]; Distance [NM oder \
            Tmmm fuer Minuten]; Vertical Speed [ft/min]; Profile Climb Step \
            [ft]; HWC/TWC [Kts]; delta T ISA [K]
        Type; FL; Ma/CAS [Ma oder Kxxx fuer Knoten CAS]; Distance [NM oder \
            Tmmm fuer Minuten]; Vertical Speed [ft/min]; Profile Climb Step \
            [ft]; HWC/TWC [Kts]; delta T ISA [K]

        """
        logging.debug("exporting flight path to FX csv..")

        aircraft_name = str(self.cbAircraft.currentText())  # convert from QString
        if aircraft_name == '':
            return
        aircraft_config = str(self.cbAircraftConfig.currentText())
        if aircraft_config == '':
            return

        # Get the aircraft object.
        aircraft = performance.available_aircraft[aircraft_name]

        takeoff_time = self.dteTakeoffTime.dateTime().toPyDateTime()
        takeoff_weight = self.sbTakeoffWeight.value()

        logging.debug("aircraft: %s (%s)" % (aircraft_name, aircraft_config))
        logging.debug("takeoff at %s with weight %i lbs" %
                      (takeoff_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       takeoff_weight))

        # Compute fuel weight.
        zero_fuel_weight_lbs = aircraft.maximumTakeoffWeight_lbs - aircraft.fuelCapacity_lbs
        fuel_weight_lbs = takeoff_weight - zero_fuel_weight_lbs

        # Get waypoints of the current flight track.
        waypoints = self.model.allWaypointData(mode=ft.USER)
        if len(waypoints) < 3:
            logging.error("for performance computations, the flight track "
                          "must consist of at least three waypoints.")
            return

        # Setup an initial flight track description for the performance module.
        flight_description_csv = [
            "General Input",
            "%i;%i;%i;%f;%i;%i;%f;%f" %
            (zero_fuel_weight_lbs,  # zero fuel weight [lbs]
             fuel_weight_lbs,  # takeoff fuel [lbs]
             3000,  # reserve fuel [lbs]
             waypoints[-1].distance_total / 1.852,  # total flight distance [nm]
             waypoints[0].flightlevel * 100.,  # takeoff altitude [ft]
             waypoints[-1].flightlevel * 100.,  # landing alt
             waypoints[0].lon,  # takeoff position
             waypoints[0].lat),  # takeoff position
            "HALO Configuration",
            "0;0;0;0;0;0;0;0;0;0;0;0",
            "Flight Legs"
        ]

        # Loop over waypoints 1..N-1 (omitting takoff and landing waypoints 0
        # and N) and output the segments between waypoints n-1 .. n. All
        # segments are defined as "Level" segments; Johannes' performance module
        # automatically changes to climb/descent if required.
        for waypoint in waypoints[1:-1]:

            # Automatic flight mode: First waypoint is takeoff, all other
            # waypoints are level flights.
            flight_type = "Level"
            if waypoint == waypoints[1]:
                flight_type = "Initial Climb"

            # Predefined speed selection (see email Johannes 26Apr2013):
            #           < FL100 : K250 = 250 knots IAS
            #     FL100 - FL280 : K280 = 280 knots
            #           > FL280 : 0.8  = Mach 0.8

            speed_indicator = "K250"
            if waypoint.flightlevel > 100:
                speed_indicator = "K280"
            if waypoint.flightlevel > 280:
                speed_indicator = "0.8"

            # Second-to-last waypoint: Top Of Descent (TOD) instead of
            # segment length.
            segment_length_nm = "%f" % (waypoint.distance_to_prev / 1.852)
            if waypoint == waypoints[-2]:
                segment_length_nm = "TOD"

            flight_description_csv.append(
                "%s;%i;%s;%s;;;;;%f;%f" %
                (flight_type,
                 waypoint.flightlevel,  # flight level
                 speed_indicator,  # aircraft speed
                 segment_length_nm,  # segment length [nm]
                 waypoint.lon,  # segment position
                 waypoint.lat)
            )

        # Output final decent to destination airport.
        waypoint = waypoints[-1]
        flight_description_csv.append(
            "Final Descent;;;;1500;;0;0;%f;%f" %
            (waypoint.lon,  # segment position
             waypoint.lat)
        )

        # Ask the user for a filename.
        filename = QtGui.QFileDialog.getSaveFileName(
            self, "Save Flight Profile", "", "FX CSV (*.csv)")
        if not filename.isEmpty():
            # Write the list to an output file.
            filename = str(filename)
            if not filename.endswith(".csv"):
                filename += ".csv"
            logging.debug("Writing profile to file %s..." % filename)
            csvfile = open(filename, "w")
            for item in flight_description_csv:
                csvfile.write("%s\n" % item)
            csvfile.close()

        logging.debug("Done.")


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
    win = PerformanceControlWidget(default_FPS=mss_settings.default_VSEC_WMS,
                                   model=waypoints_model)
    win.show()
    sys.exit(app.exec_())
