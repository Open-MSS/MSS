"""Control widget to access Web Map Services.

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

* Marc Rautenhaus

"""

# standard library imports
import urllib
import urllib2
from datetime import datetime, timedelta
import xml.etree.ElementTree as etree
import re
import logging
import StringIO
import threading
import Queue
import os
import hashlib
import time

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings
import owslib.wms
import owslib.util
import PIL.Image

# local application imports
import ui_wms_dockwidget as ui
import ui_wms_password_dialog as ui_pw
import wms_capabilities
import mss_settings
import wms_login_cache
from mslib.mss_util import convertHPAToKM

################################################################################
###                   Settings imported from mss_settings                    ###
################################################################################

default_WMS = mss_settings.default_WMS
default_VSEC_WMS = mss_settings.default_VSEC_WMS
wms_cache = mss_settings.wms_cache


################################################################################
###                          CLASS MSSWebMapService                          ###
################################################################################

class MSSWebMapService(owslib.wms.WebMapService):
    """Overloads the getmap() method of owslib.wms.WebMapService:

        added parameters are
         init_time
         level
         path_str

        the function times out after wms_timeout seconds. 
    """

    def getmap(self, layers=None, styles=None, srs=None, bbox=None,
               format=None, size=None, time=None, init_time=None,
               path_str=None, level=None, transparent=False,
               bgcolor='#FFFFFF', time_format="%Y-%m-%dT%H:%M:%SZ",
               init_time_format="%Y-%m-%dT%H:%M:%SZ",
               time_name="time", init_time_name="init_time",
               exceptions='application/vnd.ogc.se_xml', method='Get',
               return_only_url=False):
        """Request and return an image from the WMS as a file-like object.
        
        Parameters
        ----------
        layers : list
            List of content layer names.
        styles : list
            Optional list of named styles, must be the same length as the
            layers list.
        srs : string
            A spatial reference system identifier.
        bbox : tuple
            (left, bottom, right, top) in srs units.
        format : string
            Output image format such as 'image/jpeg'.
        size : tuple
            (width, height) in pixels.
        transparent : bool
            Optional. Transparent background if True.
        bgcolor : string
            Optional. Image background color.
        method : string
            Optional. HTTP DCP method name: Get or Post.
        
        Example
        -------
            >>> img = wms.getmap(layers=['global_mosaic'],
            ...                  styles=['visual'],
            ...                  srs='EPSG:4326', 
            ...                  bbox=(-112,36,-106,41),
            ...                  format='image/jpeg',
            ...                  size=(300,250),
            ...                  transparent=True,
            ...                  )
            >>> out = open('example.jpg', 'wb')
            >>> out.write(img.read())
            >>> out.close()

        """
        base_url = self.getOperationByName('GetMap').methods[method]['url']
        request = {'version': self.version, 'request': 'GetMap'}

        # check layers and styles
        assert len(layers) > 0
        request['layers'] = ','.join(layers)
        if styles:
            assert len(styles) == len(layers)
            request['styles'] = ','.join(styles)
        else:
            request['styles'] = ''

        # size
        request['width'] = str(size[0])
        request['height'] = str(size[1])

        request['srs'] = str(srs)
        request['format'] = str(format)
        request['transparent'] = str(transparent).upper()
        request['bgcolor'] = '0x' + bgcolor[1:7]
        request['exceptions'] = str(exceptions)

        # ++(mss)
        if bbox is not None:
            request['bbox'] = ','.join([str(x) for x in bbox])
        if path_str is not None:
            request['path'] = path_str

        # According to the WMS 1.1.1 standard, dimension names must be
        # prefixed with a "dim_", except for the in the standard predefined
        # dimensions "time" and "elevation".
        time_name = time_name if time_name == "time" else "dim_" + time_name
        init_time_name = "dim_" + init_time_name

        # If the parameters time and init_time are given as datetime objects,
        # create formatted strings with the given formatter. If they are
        # given as strings, use these strings directly as WMS arguments.
        if type(time) is datetime:
            if time_format is None:
                raise ValueError("Could not determine date/time format. Please "
                                 "check dimension tag in capabiltites document.")
            request[time_name] = time.strftime(time_format)
        elif type(time) is str:
            request[time_name] = time
        if type(init_time) is datetime:
            if init_time_format is None:
                raise ValueError("Could not determine date/time format. Please "
                                 "check dimension tag in capabiltites document.")
            request[init_time_name] = init_time.strftime(init_time_format)
        elif type(init_time) is str:
            request[init_time_name] = init_time

        if level is not None:
            request['elevation'] = str(level)
        # --(mss)

        data = urllib.urlencode(request)

        # ++(mss)
        base_url = base_url.replace("ogctest.iblsoft", "ogcie.iblsoft")  # IBL Bugfix!
        base_url = base_url.replace("ogcie/obs", "ogcie.iblsoft.com/obs")  # IBL Bugfix!
        base_url = base_url.replace(", staging1", "")  # geo.beopen.eu bugfix
        complete_url = "%s%s" % (base_url, data)
        if return_only_url:
            return complete_url
        logging.debug("Retrieving: %s" % complete_url)
        # --(mss)

        # (mss) owslib.util.openURL checks for ServiceExceptions and raises a
        # owslib.wms.ServiceException. However, openURL only checks for mime
        # types text/xml and application/xml. application/vnd.ogc.se_xml is
        # not considered. For some reason, the check below doesn't work, though..

        u = owslib.util.openURL(base_url, data, method,
                                username=self.username,
                                password=self.password)

        # check for service exceptions, and return
        if hasattr(u, "info"):
            # NOTE: There is little bug in owslib.util.openURL -- if the file
            # returned by the http server is an XML file, urlopen converts it
            # into an "RereadableURL" object. WHile this enables the URL content
            # to be scanned in urlopen as well as in a following method
            # (urllib2.urlopen objects only allow the content to be read once),
            # the "info" attribute is missing after the conversion..
            if u.info()['Content-Type'] == 'application/vnd.ogc.se_xml':
                se_xml = u.read()
                se_tree = etree.fromstring(se_xml)
                err_message = str(se_tree.find('ServiceException').text).strip()
                raise owslib.wms.ServiceException(err_message, se_xml)
        return u


################################################################################
###                      DIALOG for WMS Authentication                       ###
################################################################################

class MSS_WMS_AuthenticationDialog(QtGui.QDialog, ui_pw.Ui_WMSAuthenticationDialog):
    """Dialog to ask the user for username/password should this be
       required by a WMS server.
    """

    def __init__(self, parent=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        """
        super(MSS_WMS_AuthenticationDialog, self).__init__(parent)
        self.setupUi(self)

    def getAuthInfo(self):
        """Return the entered username and password.
        """
        return (str(self.leUsername.text()),
                str(self.lePassword.text()))


################################################################################
###                        CLASS WMSControlWidget                            ###
################################################################################

class WMSControlWidget(QtGui.QWidget, ui.Ui_WMSDockWidget):
    """The base class of the WMS control widget: Provides the GUI
       elements and common functionality to access a WMS. This class
       is not instantiated directly, see HSecWMSControlWidget and
       VSecWMSControlWidget below.

    NOTE: Currently this class can only handle WMS 1.1.1 servers.
    """

    def __init__(self, parent=None, crs_filter=".*",
                 default_WMS=[], wms_cache=None, view=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        crs_filter -- display only those layers in the 'Layers' combobox
                      whose names match this regexp. Can be used to filter
                      layers. Default is to display all layers.
        default_WMS -- list of strings that specify WMS URLs that will be
                       displayed in the URL combobox as default values.
        """
        super(WMSControlWidget, self).__init__(parent)
        self.setupUi(self)

        self.view = view

        # Accomodates MSSWebMapService instances.
        self.wms = None

        # Initial list of WMS servers.
        self.cbWMS_URL.clear()
        self.cbWMS_URL.addItems(default_WMS)

        # Compile regular expression used in crsAllowed() to filter
        # layers accordings to their CRS.
        self.crs_filter = re.compile(crs_filter)

        # Initially allowed WMS parameters and date/time formats.
        self.allowed_init_times = []
        self.allowed_valid_times = []
        self.init_time_format = "%Y-%m-%dT%H:%M:%SZ"
        self.valid_time_format = "%Y-%m-%dT%H:%M:%SZ"
        self.init_time_name = ""
        self.valid_time_name = ""

        self.layerChangeInProgress = False

        # Initialise GUI elements that control WMS parameters.
        self.cbLayer.clear()
        self.cbStyle.clear()
        self.cbLevel.clear()
        self.cbInitTime.clear()
        self.cbValidTime.clear()

        self.time_steps = ["1 min", "5 min", "10 min", "15 min", "30 min",
                           "1 hour", "2 hours", "3 hours", "6 hours",
                           "12 hours", "24 hours", "2 days", "7 days"]
        self.cbInitTime_step.clear()
        self.cbInitTime_step.addItems(self.time_steps)
        self.cbInitTime_step.setCurrentIndex(self.cbInitTime_step.findText("12 hours"))
        self.cbValidTime_step.clear()
        self.cbValidTime_step.addItems(self.time_steps)
        self.cbValidTime_step.setCurrentIndex(self.cbInitTime_step.findText("3 hours"))

        self.enableLevelElements(False)
        self.enableValidTimeElements(False)
        self.enableInitTimeElements(False)
        self.btGetMap.setEnabled(False)
        self.tbViewCapabilities.setEnabled(False)
        self.cbTransparent.setChecked(False)

        # Check for WMS image cache directory, create if neceassary.
        if wms_cache is not None:
            self.wms_cache = os.path.join(wms_cache, "")
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

        # Initialise date/time fields with current day, 00 UTC.
        self.dteInitTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0,
                                      microsecond=0)))
        self.dteValidTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0,
                                      microsecond=0)))

        # Connect slots and signals.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.connect(self.btGetCapabilities, QtCore.SIGNAL("clicked()"),
                     self.getCapabilities)
        self.connect(self.tbViewCapabilities, QtCore.SIGNAL("clicked()"),
                     self.viewCapabilities)

        self.connect(self.cbLayer, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.layerChanged)

        self.connect(self.cbLevel, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.levelChanged)
        # Connecting both activated() and currentIndexChanged() signals leads
        # to **TimeChanged() being called twice when the user selects a new
        # item in the combobox. However, currentIndexChanged alone doesn't
        # trigger the event when the user selects the currently active item
        # (e.g. to confirm the time). activated() doesn't trigger the event
        # if the index has been changed programmatically (e.g. through the
        # back/forward buttons).
        self.connect(self.cbInitTime, QtCore.SIGNAL("activated(int)"),
                     self.initTimeChanged)
        # self.connect(self.cbInitTime, QtCore.SIGNAL("currentIndexChanged(int)"),
        #             self.initTimeChanged)
        self.connect(self.cbValidTime, QtCore.SIGNAL("activated(int)"),
                     self.validTimeChanged)
        # self.connect(self.cbValidTime, QtCore.SIGNAL("currentIndexChanged(int)"),
        #             self.validTimeChanged)

        self.connect(self.tbInitTime_back, QtCore.SIGNAL("clicked()"),
                     self.init_time_back_click)
        self.connect(self.tbInitTime_fwd, QtCore.SIGNAL("clicked()"),
                     self.init_time_fwd_click)
        self.connect(self.tbInitTime_cbback, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_back_click)
        self.connect(self.tbInitTime_cbfwd, QtCore.SIGNAL("clicked()"),
                     self.cb_init_time_fwd_click)
        self.connect(self.dteInitTime, QtCore.SIGNAL("dateTimeChanged(const QDateTime&)"),
                     self.check_init_time)
        self.connect(self.tbValidTime_back, QtCore.SIGNAL("clicked()"),
                     self.valid_time_back_click)
        self.connect(self.tbValidTime_fwd, QtCore.SIGNAL("clicked()"),
                     self.valid_time_fwd_click)
        self.connect(self.tbValidTime_cbback, QtCore.SIGNAL("clicked()"),
                     self.cb_valid_time_back_click)
        self.connect(self.tbValidTime_cbfwd, QtCore.SIGNAL("clicked()"),
                     self.cb_valid_time_fwd_click)
        self.connect(self.dteValidTime, QtCore.SIGNAL("dateTimeChanged(const QDateTime&)"),
                     self.check_valid_time)
        self.connect(self.tbLevel_back, QtCore.SIGNAL("clicked()"),
                     self.level_back_click)
        self.connect(self.tbLevel_fwd, QtCore.SIGNAL("clicked()"),
                     self.level_fwd_click)

        self.connect(self.btClearCache, QtCore.SIGNAL("clicked()"),
                     self.clearCache)

        if view is not None:
            self.connect(view, QtCore.SIGNAL("redrawn()"),
                         self.afterRedraw)

        # Progress dialog to inform the user about image ongoing retrievals.
        self.pdlg = QtGui.QProgressDialog("retrieving image...", "Cancel",
                                          0, 10, self)

    def __del__(self):
        """Destructor.
        """
        # Service the WMS cache on application exit.
        if self.wms_cache is not None:
            self.serviceCache()

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
                    if str(ex).startswith("401") or str(ex).find("Error 401") >= 0 or str(ex).find(
                            "401 Unauthorized") >= 0:
                        # Catch the "401 Unauthorized" error if one has been
                        # returned by the server and ask the user for username
                        # and password.
                        # WORKAROUND (mr, 28Mar2013) -- owslib doesn't recognize
                        # the Apache 401 messages, we get an XML message here but
                        # no error code. Quick workaround: Scan the XML message for
                        # the string "Error 401"...
                        dlg = MSS_WMS_AuthenticationDialog(parent=self)
                        dlg.setModal(True)
                        if dlg.exec_() == QtGui.QDialog.Accepted:
                            username, password = dlg.getAuthInfo()
                            if username == '':
                                # If the username was left blank, restore the
                                # last cached value, if available.
                                if wms_login_cache.cached_usrname is not None:
                                    username = wms_login_cache.cached_usrname
                                    password = wms_login_cache.cached_passwd
                            else:
                                # If user & pw have been entered, cache them.
                                wms_login_cache.cached_usrname = username
                                wms_login_cache.cached_passwd = password
                        else:
                            break
                    else:
                        raise
        except Exception as ex:
            logging.error("ERROR: %s", ex)
            logging.error("cannot load capabilities document.. "
                          "no layers can be used in this view.")
            QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
        return wms

    def getCapabilities(self):
        """Query the WMS server in the URL combobox for its capabilities. Fill
           layer, style, etc. combo boxes.
        """
        # Clear layer and style combo boxes. First disconnect the layerChanged
        # slot to avoid calls to this function.
        self.disconnect(self.cbLayer, QtCore.SIGNAL("currentIndexChanged(int)"),
                        self.layerChanged)
        self.cbLayer.clear()
        self.cbStyle.clear()

        # Load new WMS. Only add those layers to the combobox that can provide
        # the CRS that match the filter of this module.
        base_url = str(self.cbWMS_URL.currentText())
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
                        # cb_string = "%s | %s" % (layer.name, layer.title)
                        cb_string = "%s | %s" % (layer.title, layer.name)
                        if cb_string not in filtered_layers:
                            filtered_layers.append(cb_string)
                else:
                    stack.extend(layer.layers)
            logging.debug("discovered %i layers that can be used in this view" %
                          len(filtered_layers))
            filtered_layers.sort()
            self.cbLayer.addItems(filtered_layers)
            self.wms = wms
            self.layerChanged(0)
            self.btGetMap.setEnabled(True)
            self.tbViewCapabilities.setEnabled(True)

        # Reconnect layerChanged.
        self.connect(self.cbLayer, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.layerChanged)

    def viewCapabilities(self):
        """Open a WMSCapabilitiesBrowser dialog showing the capabilities
           document.
        """
        logging.debug("Opening WMS capabilities browser..")
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

    def layerChanged(self, index):
        """Slot that updates the <cbStyle> and <teLayerAbstract> GUI elements
           when the user selects a new layer in <cbLayer>.
        """
        layer = self.getLayer()
        if not self.wms or layer == '':
            # Do not execute this method if no WMS has been registered or no
            # layer is available (layer will be an empty string then).
            return
        self.layerChangeInProgress = True  # Flag for autoUpdate()
        layerobj = self.get_layer_object(layer)
        styles = layerobj.styles
        self.cbStyle.clear()
        self.cbStyle.addItems(["%s | %s" % (s, styles[s]["title"])
                               for s in styles])
        abstract_text = layerobj.abstract if layerobj.abstract else ""
        abstract_text = ' '.join([s.strip() for s in abstract_text.splitlines()])
        self.teLayerAbstract.setText(abstract_text)

        # Handle dimensions:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        save_init_time = self.dteInitTime.dateTime()
        save_valid_time = self.dteValidTime.dateTime()

        enable_elevation = False
        enable_inittime = False
        enable_validtime = False
        self.cbLevel.clear()
        self.cbInitTime.clear()
        self.cbValidTime.clear()
        # ~~~~ A) Elevation. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        lobj = layerobj
        while lobj is not None:
            if "elevation" in lobj.dimensions.keys() and \
                            "elevation" in lobj.extents.keys():
                units = lobj.dimensions["elevation"]["units"]
                elev_list = ["%s (%s)" % (e.strip(), units) for e in
                             lobj.extents["elevation"]["values"]]
                self.cbLevel.addItems(elev_list)
                enable_elevation = True
                break

            # One step up in the level hierarchy: If no dimension values
            # were identified, check if this layer inherits some from its
            # parent.
            lobj = lobj.parent

        # ~~~~ B) Initialisation time. ~~~~~~~~~~~~~~~~~~~~~~~~
        self.allowed_init_times = []
        self.init_time_format = None

        lobj = layerobj
        while lobj is not None:
            if "init_time" in lobj.dimensions.keys() and \
                            "init_time" in lobj.extents.keys():
                # MSS web map service.
                self.init_time_name = "init_time"
                enable_inittime = True
            elif "run" in lobj.dimensions.keys() and \
                            "run" in lobj.extents.keys():
                # IBL web map service.
                self.init_time_name = "run"
                enable_inittime = True

            # Initialisation tag was found: Try to determine the format of
            # the date/time strings and read the provided extent values.
            # Add the extent values to the init time combobox.
            if enable_inittime:
                self.init_time_format = self.interpret_timestring(
                    lobj.extents[self.init_time_name]["values"][0].strip(),
                    return_format=True)
                if self.init_time_format is not None:
                    # (otherwise self.init_time_format remains an emtpy list)
                    self.allowed_init_times = [datetime.strptime(val.strip(), self.init_time_format)
                                               for val in lobj.extents[self.init_time_name]["values"]]
                self.cbInitTime.addItems(lobj.extents[self.init_time_name]["values"])
                break

            # One step up in the level hierarchy: If no dimension values
            # were identified, check if this layer inherits some from its
            # parent.
            lobj = lobj.parent

        # ~~~~ C) Valid/forecast time. ~~~~~~~~~~~~~~~~~~~~~~~~~
        self.cbValidOn.setToolTip("")
        font = self.cbValidOn.font()
        font.setBold(False)
        self.cbValidOn.setFont(font)
        vtime_no_extent = False
        self.allowed_valid_times = []
        self.valid_time_format = None

        lobj = layerobj
        while lobj is not None:

            if "time" in lobj.dimensions.keys() and \
                            "time" in lobj.extents.keys():
                self.valid_time_name = "time"
                enable_validtime = True
            elif "time" in lobj.dimensions.keys():
                enable_validtime = True
                self.valid_time_name = "time"
                vtime_no_extent = True
            elif "forecast" in lobj.dimensions.keys() and \
                            "forecast" in lobj.extents.keys():
                # IBL web map service.
                self.valid_time_name = "forecast"
                enable_validtime = True

            # Both time dimension and time extent tags were found. Try to determine the
            # format of the date/time strings.
            if enable_validtime and not vtime_no_extent:
                items = [i.strip() for i in lobj.extents[self.valid_time_name]["values"]]
                if len(items) > 0:
                    if items[0].find("/") > 0:
                        # A "/" indicates a time range. Do NOT put any
                        # values in the combo box and try to determine the time
                        # format. Times are specified only by the date/time element
                        # in this case.
                        self.valid_time_format = self.interpret_timestring(items[0].split("/")[0],
                                                                           return_format=True)
                        font = self.cbValidOn.font()
                        font.setBold(True)
                        self.cbValidOn.setFont(font)
                        self.cbValidOn.setToolTip(items[0])
                        vtime_no_extent = True

                    else:  # (no time range)
                        # Determine time format and try to determine allowed times.
                        self.valid_time_format = self.interpret_timestring(items[0],
                                                                           return_format=True)

                        # Loop over all time items provided by the server:
                        self.allowed_valid_times = []
                        for time_item in items:
                            interpretation_successful = True

                            if time_item.find("/") > 0:
                                # This item describes a list of time
                                # values. Expand the list.
                                list_desc = time_item.split("/")
                                # We need three entries: start time, end time,
                                # time interval.
                                if len(list_desc) != 3:
                                    interpretation_successful = False

                                try:
                                    time_val = datetime.strptime(list_desc[0],
                                                                 self.valid_time_format)
                                    end_time = datetime.strptime(list_desc[1],
                                                                 self.valid_time_format)
                                    # Parse interval strings of format "PT3H" (= 3 hours)
                                    # or "PT24H" (24 hours).
                                    time_interval_hours = int(re.match("PT(\d+)H",
                                                                       list_desc[2]).group(1))

                                    # Register all time values of the list.
                                    while time_val <= end_time:
                                        self.allowed_valid_times.append(time_val)
                                        self.cbValidTime.addItem(
                                            time_val.strftime(self.valid_time_format))
                                        time_val += timedelta(hours=time_interval_hours)

                                except:
                                    interpretation_successful = False

                            else:
                                # Single item, no list.
                                try:
                                    self.allowed_valid_times.append(
                                        datetime.strptime(time_item,
                                                          self.valid_time_format))
                                    self.cbValidTime.addItem(time_item)
                                except:
                                    interpretation_successful = False

                            if not interpretation_successful:
                                logging.error("Can't understand time string %s."
                                              " Please check the implementation." % time_item)

            # No time extent tag was found: Set allowed_valid_times to None
            # (used by validTimeChanged()).
            if vtime_no_extent:
                self.allowed_valid_times = None

            if enable_validtime:
                break

            # One step up in the level hierarchy: If no dimension values
            # were identified, check if this layer inherits some from its
            # parent.
            lobj = lobj.parent

        logging.debug("determined init time format: %s", self.init_time_format)
        if enable_inittime and self.init_time_format is None:
            msg = "cannot determine init time format."
            logging.warning("WARNING: %s" % msg)
            if self.cbInitTime.count() == 0:
                # If no values could be read from the extent tag notify
                # the user.
                QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                           self.tr("ERROR: %s" % msg),
                                           QtGui.QMessageBox.Ok)
            self.init_time_format = ""

        logging.debug("determined valid time format: %s", self.valid_time_format)
        if enable_validtime and self.valid_time_format is None:
            msg = "cannot determine valid time format."
            logging.warning("WARNING: %s" % msg)
            if self.cbValidTime.count() == 0:
                # If no values could be read from the extent tag notify
                # the user.
                QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                           self.tr("ERROR: %s" % msg),
                                           QtGui.QMessageBox.Ok)
            self.valid_time_format = ""

        self.enableLevelElements(enable_elevation)
        self.enableValidTimeElements(enable_validtime)
        self.enableInitTimeElements(enable_inittime)

        # Check whether dimension strings can be interpreted. If not, disable
        # the sync to the date/time elements.
        if not self.initTimeChanged():
            self.disableDTEInitTimeElements()
        if not self.validTimeChanged():
            self.disableDTEValidTimeElements()
        if self.cbInitTime.count() == 0:
            self.disableCBInitTimeElements()
        if self.cbValidTime.count() == 0:
            self.disableCBValidTimeElements()

        # Try to restore previous time settings. Setting the date/time edits
        # triggers a signal to calls check_(init/valid)_time(), however, the
        # method is only called if the date actually changes (i.e. the layer
        # has provided time values, these were inserted into the combobox,
        # and via the combobox-signal the datetime edit was changed). This
        # can lead to a strike through font if the new layer does not provide
        # time values. Therefore the additional call to check_*_time().
        self.dteInitTime.setDateTime(save_init_time)
        self.check_init_time(save_init_time)
        self.dteValidTime.setDateTime(save_valid_time)
        self.check_valid_time(save_valid_time)
        self.layerChangeInProgress = False

    def secs_from_timestep(self, timestep_string):
        """Convert a string specifying a time step (e.g. 5 min, 3 hours) to
           seconds.

        Allowed formats:
         a) 'XX min', where XX is an integer.
         b) 'XX hours', where XX is an integer.
         c) 'XX days', where XX is an integer.
        """
        try:
            minutes = int(timestep_string.split(" min")[0])
            return minutes * 60
        except:
            pass
        try:
            hours = int(timestep_string.split(" hour")[0])
            return hours * 3600
        except:
            pass
        try:
            days = int(timestep_string.split(" days")[0])
            return days * 86400
        except:
            raise ValueError("cannot convert %s to seconds: wrong format."
                             % timestep_string)

    def init_time_back_click(self):
        """Slot for the tbInitTime_back button.
        """
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteInitTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(str(self.cbInitTime_step.currentText()))
        self.dteInitTime.setDateTime(d.addSecs(-1. * secs))
        self.autoUpdate()

    def init_time_fwd_click(self):
        """Slot for the tbInitTime_fwd button.
        """
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteInitTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(str(self.cbInitTime_step.currentText()))
        self.dteInitTime.setDateTime(d.addSecs(secs))
        self.autoUpdate()

    def valid_time_back_click(self):
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteValidTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(str(self.cbValidTime_step.currentText()))
        self.dteValidTime.setDateTime(d.addSecs(-1. * secs))
        self.autoUpdate()

    def valid_time_fwd_click(self):
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteValidTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(str(self.cbValidTime_step.currentText()))
        self.dteValidTime.setDateTime(d.addSecs(secs))
        self.autoUpdate()

    def level_back_click(self):
        ci = self.cbLevel.currentIndex()
        if ci > 0:
            ci = ci - 1
        self.cbLevel.setCurrentIndex(ci)

    def level_fwd_click(self):
        ci = self.cbLevel.currentIndex()
        if ci < self.cbLevel.count() - 1:
            ci = ci + 1
        self.cbLevel.setCurrentIndex(ci)

    def cb_init_time_back_click(self):
        ci = self.cbInitTime.currentIndex()
        if ci > 0:
            ci = ci - 1
        self.cbInitTime.setCurrentIndex(ci)
        self.initTimeChanged()

    def cb_init_time_fwd_click(self):
        ci = self.cbInitTime.currentIndex()
        if ci < self.cbInitTime.count() - 1:
            ci = ci + 1
        self.cbInitTime.setCurrentIndex(ci)
        self.initTimeChanged()

    def cb_valid_time_back_click(self):
        ci = self.cbValidTime.currentIndex()
        if ci > 0:
            ci = ci - 1
        self.cbValidTime.setCurrentIndex(ci)
        self.validTimeChanged()

    def cb_valid_time_fwd_click(self):
        ci = self.cbValidTime.currentIndex()
        if ci < self.cbValidTime.count() - 1:
            ci = ci + 1
        self.cbValidTime.setCurrentIndex(ci)
        self.validTimeChanged()

    def autoUpdate(self):
        """If the auto update check box is checked, let btGetMap emit a
           clicked() signal everytime this method is called.
           autoUpdate() should be called from the slots that handle
           time and level changes.

        If the the layerChangeInProgress flag is set no update will be
        performed (lock mechanism to prevent erroneous requests during
        a layer change).
        """
        if self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
            self.btGetMap.click()

    def check_init_time(self, dt):
        """Checks whether an initialisation time set with the init time
           date/time edit is contained in the list of init times advertised
           by the WMS server.

        If the time is not contained in the list, the font will be set to
        'strike through' to indicate an invalid time.
        """
        font = self.dteInitTime.font()
        inittime_available = dt.toPyDateTime() in self.allowed_init_times
        font.setStrikeOut(not inittime_available)
        self.dteInitTime.setFont(font)
        if inittime_available:
            iso8601_time = dt.toPyDateTime().strftime(self.init_time_format)
            index = self.cbInitTime.findText(iso8601_time)
            self.cbInitTime.setCurrentIndex(index)

    def check_valid_time(self, dt):
        """Same as check_init_time, but for valid time.
        """
        font = self.dteValidTime.font()
        if self.allowed_valid_times is not None:
            validtime_available = dt.toPyDateTime() in self.allowed_valid_times
        else:
            validtime_available = True
        font.setStrikeOut(not validtime_available)
        self.dteValidTime.setFont(font)
        if validtime_available:
            iso8601_time = dt.toPyDateTime().strftime(self.valid_time_format)
            index = self.cbValidTime.findText(iso8601_time)
            # setCurrentIndex also sets the date/time edit via signal.
            self.cbValidTime.setCurrentIndex(index)

    def initTimeChanged(self):
        """Slot to be called when the current index of the init time
           combo box is changed. The method tries to sync to the
           init time date/time edit.
        """
        init_time = str(self.cbInitTime.currentText())
        if init_time != "":
            init_time = self.interpret_timestring(init_time)
            if init_time is not None:
                self.dteInitTime.setDateTime(init_time)
        self.autoUpdate()
        return (init_time == "" or init_time is not None)

    def validTimeChanged(self):
        """Same as initTimeChanged(), but for the valid time elements.
        """
        valid_time = str(self.cbValidTime.currentText())
        if valid_time != "":
            valid_time = self.interpret_timestring(valid_time)
            if valid_time is not None:
                self.dteValidTime.setDateTime(valid_time)
        self.autoUpdate()
        return (valid_time == "" or valid_time is not None)

    def levelChanged(self):
        self.autoUpdate()

    def enableLevelElements(self, enable):
        """Enable or disable the GUI elements allowing vertical elevation
           level control.
        """
        self.cbLevelOn.setChecked(enable)
        self.cbLevel.setEnabled(enable)
        self.tbLevel_back.setEnabled(enable)
        self.tbLevel_fwd.setEnabled(enable)

    def enableInitTimeElements(self, enable):
        """Enables or disables the GUI elements allowing initialisation time
           control.
        """
        self.cbInitialisationOn.setChecked(enable)
        self.cbInitTime.setEnabled(enable)
        self.dteInitTime.setEnabled(enable)
        self.tbInitTime_back.setEnabled(enable)
        self.tbInitTime_fwd.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)
        self.cbInitTime_step.setEnabled(enable)

    def enableValidTimeElements(self, enable):
        """Enables or disables the GUI elements allowing valid time
           control.
        """
        self.cbValidOn.setChecked(enable)
        self.cbValidTime.setEnabled(enable)
        self.dteValidTime.setEnabled(enable)
        self.tbValidTime_back.setEnabled(enable)
        self.tbValidTime_fwd.setEnabled(enable)
        self.tbValidTime_cbback.setEnabled(enable)
        self.tbValidTime_cbfwd.setEnabled(enable)
        self.cbValidTime_step.setEnabled(enable)

    def disableDTEInitTimeElements(self):
        """Disables init time date/time edit elements.
        """
        enable = False
        self.dteInitTime.setEnabled(enable)
        self.tbInitTime_back.setEnabled(enable)
        self.tbInitTime_fwd.setEnabled(enable)
        self.cbInitTime_step.setEnabled(enable)

    def disableDTEValidTimeElements(self):
        """Disables valid time date/time edit elements.
        """
        enable = False
        self.dteValidTime.setEnabled(enable)
        self.tbValidTime_back.setEnabled(enable)
        self.tbValidTime_fwd.setEnabled(enable)
        self.cbValidTime_step.setEnabled(enable)

    def disableCBInitTimeElements(self):
        """Disables init time combobox elements.
        """
        enable = False
        self.cbInitTime.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)

    def disableCBValidTimeElements(self):
        """Disables valid time combobox elements.
        """
        enable = False
        self.cbValidTime.setEnabled(enable)
        self.tbValidTime_cbback.setEnabled(enable)
        self.tbValidTime_cbfwd.setEnabled(enable)

    def getLayer(self):
        return unicode(self.cbLayer.currentText(), errors="ignore").split(" | ")[-1]

    def getStyle(self):
        return unicode(self.cbStyle.currentText(), errors="ignore").split(" |")[0]

    def getLevel(self):
        if self.cbLevelOn.isChecked():
            return unicode(self.cbLevel.currentText(), errors="ignore").split(" (")[0]
        else:
            return None

    def getInitTime(self):
        """Get the initialisation time from the GUI elements.

        If the init time date/time edit is enabled (i.e. the times specifed
        in the WMS capabilities document can be interpreted), return a
        datetime object of the currently set time. Otherwise, return the
        string that is selected in the init time combobox.
        """
        if self.cbInitialisationOn.isChecked():
            if self.dteInitTime.isEnabled():
                return self.dteInitTime.dateTime().toPyDateTime()
            else:
                itime_str = str(self.cbInitTime.currentText())
                return itime_str
        else:
            return None

    def getValidTime(self):
        """The same as getInitTime(), but for the valid time.
        """
        if self.cbValidOn.isChecked():
            if self.dteValidTime.isEnabled():
                return self.dteValidTime.dateTime().toPyDateTime()
            else:
                vtime_str = str(self.cbValidTime.currentText())
                return vtime_str
        else:
            return None

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

    def retrieveImage(self, crs="EPSG:4326", bbox=None, path_string=None,
                      width=800, height=400):
        """Retrieve an image of the layer currently selected in the
           GUI elements from the current WMS provider. If caching is
           enabled, first check the cache for the requested image. If
           the image is retrieved from the WMS and caching is enabled,
           store the image into the cache.  
           If a legend graphic is available for the layer, this image
           is also retrieved.

        Arguments: 
        crs -- coordinate reference system as a string passed to the WMS
        path_string -- string of waypoints that resemble a vertical
                       section path. Can be omitted for horizontal
                       sections.
        bbox -- bounding box as list of four floats
        width, height -- width and height of requested image in pixels

        Returns: a lot..
        return img, legend_img, layer, style, init_time, valid_time, complete_level
        with
        img, legend_img -- PIL image objects
        layer, style, complete_level -- string objects
        init_time, valid_time -- datetime objects
        """

        # Show the progress dialog, (a) since the retrieval can take a few
        # seconds, and (b) to allow for cancellation of the request by the
        # user.
        self.pdlg.setValue(0)
        self.pdlg.setModal(True)
        self.pdlg.reset()

        # Stores the image to be returned. If an error occurs, None will be
        # returned.
        img = None

        # Get layer and style names.
        layer = self.getLayer()
        style = self.getStyle()
        level = self.getLevel()
        transparent = self.cbTransparent.isChecked()

        # get...Time() will return None if the corresponding checkboxes are
        # disabled. <None> objects passed to wms.getmap will not be included
        # in the query URL that is send to the server.
        init_time = self.getInitTime()
        valid_time = self.getValidTime()

        logging.debug("fetching layer %s; style %s, width %i, height %i",
                      layer, style, width, height)
        logging.debug("crs=%s, path=%s", crs, path_string)
        logging.debug("init_time=%s, valid_time=%s" % (init_time, valid_time))
        logging.debug("level=%s" % level)
        logging.debug("transparent=%s" % transparent)

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
                      "styles": [style],
                      "srs": crs,
                      "bbox": bbox,
                      "path_str": path_string,
                      "time": valid_time,
                      "init_time": init_time,
                      "level": level,
                      "time_format": self.valid_time_format,
                      "init_time_format": self.init_time_format,
                      "time_name": self.valid_time_name,
                      "init_time_name": self.init_time_name,
                      "size": (width, height),
                      "format": 'image/png',
                      "transparent": transparent}

            # If caching is enabled, get the URL and check the image cache
            # directory for the suitable image file.
            cache_hit = False
            if self.cachingEnabled():
                kwargs["return_only_url"] = True
                urlstr = self.wms.getmap(**kwargs)
                kwargs["return_only_url"] = False
                # Get an md5 digest of the URL string. The digest is used
                # as the filename.
                md5_filename = hashlib.md5(urlstr).hexdigest()
                md5_filename += ".png"
                logging.debug("checking cache for image file %s ..." %
                              md5_filename)
                md5_filename = os.path.join(self.wms_cache, md5_filename)
                if os.path.exists(md5_filename):
                    logging.debug("  file exists, loading from cache.")
                    cache_hit = True
                else:
                    logging.debug("  file does not exist, retrieving from WMS server.")

            if not cache_hit:

                self.pdlg.show();
                QtGui.QApplication.processEvents()
                self.pdlg.setValue(1);
                QtGui.QApplication.processEvents()

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

                self.pdlg.setValue(8);
                QtGui.QApplication.processEvents()
                # Read the image file from the URL into a string (urlobject.read())
                # and wrap this string into a StringIO object that behaves like a file.
                imageIO = StringIO.StringIO(urlobject.read())
                # This StringIO object can then be passed as a file substitute to
                # PIL.Image.open(). See
                #    http://www.pythonware.com/library/pil/handbook/image.htm
                img = PIL.Image.open(imageIO)
                logging.debug("layer retrieved, image size is %i bytes." % imageIO.len)
                # Store the retrieved image in the cache, if enabled.
                if self.cachingEnabled():
                    logging.debug("storing retrieved image file in cache.")
                    # Check if the image is stored as indexed palette
                    # with a transparent colour. Store correspondingly.
                    if img.mode == "P" and "transparency" in img.info.keys():
                        logging.debug("image is index colour and transparent, "
                                      "transparency index of image is %i.",
                                      img.info["transparency"])
                        img.save(md5_filename, transparency=img.info["transparency"])
                    else:
                        img.save(md5_filename)
            else:
                img = PIL.Image.open(md5_filename)
                logging.debug("layer retrieved from cache.")

        except Exception as ex:
            self.pdlg.close()
            logging.error("ERROR: %s", ex)
            QtGui.QMessageBox.critical(self, self.tr("Web Map Service"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
            raise ex

        legend_img = self.retrieveLegendGraphic()

        # Close the progress dialog and return the image.
        self.pdlg.close()

        complete_level = str(self.cbLevel.currentText())
        complete_level = complete_level if complete_level != "" else None
        return img, legend_img, layer, style, init_time, valid_time, complete_level

    def _queued_get_legend(self, queue=None, url=""):
        """Helper routine to retrieve a legend graphic from a thread: The return value
           is stored in the Queue.Queue() object that is passed to this routine,
           to be able to retrieve it after the thread has finished its
           execution.

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

    def retrieveLegendGraphic(self):
        """Retrieves the legend graphic of the currently selected layer and
           style, if available.
        """
        # Stores the image to be returned. If no legend is available, None
        # will be returned.
        img = None

        # Get layer and style names.
        layer = self.getLayer()
        style = self.getStyle()

        # Check if a legend URL has been specified.
        layerobj = self.get_layer_object(layer)
        if style != "" and "legend" in layerobj.styles[style].keys():
            urlstr = layerobj.styles[style]["legend"]
            logging.debug("fetching legend graphic from %s" % urlstr)

            # If caching is enabled, check the image cache
            # directory for the suitable image file.
            cache_hit = False
            if self.cachingEnabled():
                # Get an md5 digest of the URL string. The digest is used
                # as the filename.
                md5_filename = hashlib.md5(urlstr).hexdigest()
                md5_filename += ".png"
                logging.debug("checking cache for image file %s ..." %
                              md5_filename)
                md5_filename = os.path.join(self.wms_cache, md5_filename)
                if os.path.exists(md5_filename):
                    img = PIL.Image.open(md5_filename)
                    logging.debug("  legend graphic retrieved from cache.")
                    cache_hit = True
                else:
                    logging.debug("  file does not exist, retrieving from WMS server.")

            # Legend graphic needs to be retrieved from server.
            if not cache_hit:
                queue = Queue.Queue()
                kwargs = {"queue": queue, "url": urlstr}
                thread = threading.Thread(target=self._queued_get_legend, kwargs=kwargs)
                thread.start()

                while thread.isAlive():
                    # This loop keeps the GUI alive while the thread is executing,
                    # and checks for a cancellation request by the user.
                    QtGui.QApplication.processEvents()
                    if self.pdlg.wasCanceled():
                        logging.debug("legend retrieval was canceled by the user.")
                        raise UserWarning("legend retrieval was canceled by the user.")
                    # Wait for 10 ms if the thread is still running to prevent
                    # the application from using 100% processor time.
                    thread.join(0.01)

                # See retrieveImage()..
                if not queue.empty():
                    qreturn = queue.get()
                    if hasattr(qreturn, "read"):
                        urlobject = qreturn
                    else:
                        raise qreturn

                # Read the image file from the URL into a string (urlobject.read())
                # and wrap this string into a StringIO object that behaves like a file.
                imageIO = StringIO.StringIO(urlobject.read())
                # This StringIO object can then be passed as a file substitute to
                # PIL.Image.open(). See
                #    http://www.pythonware.com/library/pil/handbook/image.htm
                img_ = PIL.Image.open(imageIO)
                img = img_.crop(img_.getbbox())
                logging.debug("legend retrieved, legend graphic size is %i bytes." % imageIO.len)
                # Store the retrieved image in the cache, if enabled.
                if self.cachingEnabled():
                    logging.debug("storing retrieved legend graphics file in cache.")
                    try:
                        img.save(md5_filename, transparency=0)
                    except:
                        img.save(md5_filename)
        else:
            logging.debug("no legend graphic available for this layer.")

        return img

    def getMap(self):
        """Prototypical stub for getMap() function. Needs to be reimplemented
           in derived classes.
        """
        logging.error("getMap not implemented in base class.")

    def afterRedraw(self):
        """Event handler that a canvas can call after it has been redrawn.
        """
        self.autoUpdate()

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
            if (cum_size_bytes > mss_settings.wms_cache_max_size_bytes) or \
                            fage > mss_settings.wms_cache_max_age_seconds:
                os.remove(f)
                removed_files += 1

        logging.debug("cache has been cleaned (%i files removed)." % removed_files)

    ################################################################################


###                       CLASS VSecWMSControlWidget                         ###
################################################################################

class VSecWMSControlWidget(WMSControlWidget):
    """Subclass of WMSControlWidget that extends the WMS client to
       handle (non-standard) vertical sections.
    """

    def __init__(self, parent=None, crs_filter="VERT:.*",
                 default_WMS=[], waypoints_model=None,
                 view=None, wms_cache=None):
        super(VSecWMSControlWidget, self).__init__(parent=parent,
                                                   crs_filter=crs_filter,
                                                   default_WMS=default_WMS,
                                                   wms_cache=wms_cache,
                                                   view=view)
        self.waypoints_model = waypoints_model
        self.btGetMap.setText("get vertical section")
        self.connect(self.btGetMap, QtCore.SIGNAL("clicked()"),
                     self.getVSec)

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance from which the waypoints
           are obtained.
        """
        self.waypoints_model = model

    def getVSec(self):
        """Slot that retrieves the vertical section and passes the image
           to the view.
        """
        # Specify the coordinate reference system for the request. We will
        # use the non-standard "VERT:LOGP" to query the MSS WMS Server for
        # a vertical section. The vertical extent of the plot is specified
        # via the bounding box.
        crs = "VERT:LOGP"
        bbox = self.view.getBBOX()

        # Get lat/lon coordinates of flight track and convert to string for URL.
        path_string = ""
        for waypoint in self.waypoints_model.allWaypointData():
            path_string += "%.2f,%.2f," % (waypoint.lat, waypoint.lon)
        path_string = path_string[:-1]

        # Determine the current size of the vertical section plot on the
        # screen in pixels. The image will be retrieved in this size.
        width, height = self.view.getPlotSizePx()

        # Retrieve the image.
        try:
            img, legend_img, layer, style, init_time, valid_time, level = \
                self.retrieveImage(crs=crs, path_string=path_string, bbox=bbox,
                                   width=width, height=height)
        except Exception as ex:
            logging.error("an error occurred. no image retrieved. (%s)" % ex)
        else:
            # Plot the image on the view canvas.
            self.view.drawImage(img)
            if style != "":
                style_title = self.get_layer_object(layer).styles[style]["title"]
            else:
                style_title = None
            self.view.drawMetadata(title=self.get_layer_object(layer).title,
                                   init_time=init_time,
                                   valid_time=valid_time,
                                   style=style_title)


################################################################################
###                       CLASS HSecWMSControlWidget                         ###
################################################################################

class HSecWMSControlWidget(WMSControlWidget):
    """Subclass of WMSControlWidget that extends the WMS client to
       handle (standard) horizontal sections, i.e. maps.
    """

    def __init__(self, parent=None, crs_filter="EPSG:.*",
                 default_WMS=[], view=None, wms_cache=None):
        super(HSecWMSControlWidget, self).__init__(parent=parent,
                                                   crs_filter=crs_filter,
                                                   default_WMS=default_WMS,
                                                   wms_cache=wms_cache,
                                                   view=view)
        self.tp_height = None
        self.connect(self.btGetMap, QtCore.SIGNAL("clicked()"),
                     self.getMap)

    def levelChanged(self):
        if self.cbLevelOn.isChecked():
            s = unicode(self.cbLevel.currentText(), errors="ignore")
            if s == "":
                return
            lvl = float(s.split(" (")[0])
            if s.endswith("(hPa)"):
                lvl = convertHPAToKM(lvl)
            settings = self.view.getMapAppearance()
            settings["tangent_height"] = lvl
            if self.tp_height is not None:
                self.tp_height = lvl
            self.view.setMapAppearance(settings)
            if self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
                self.btGetMap.click()
            else:
                layer = self.getLayer()
                style = self.getStyle()
                if style != "":
                    style_title = self.get_layer_object(layer).styles[style]["title"]
                else:
                    style_title = None
                level = str(self.cbLevel.currentText())
                init_time = self.getInitTime()
                valid_time = self.getValidTime()
                tph = self.tp_height
                if tph is not None:
                    tph = "{:.1f} km".format(tph)
                self.view.drawMetadata(title=self.get_layer_object(layer).title,
                                       init_time=init_time,
                                       valid_time=valid_time,
                                       level=level,
                                       style=style_title,
                                       tp=tph)
                self.view.waypoints_interactor.update()

    def set_tp_height(self, height=None):
        self.tp_height = height

    def getMap(self):
        """Slot that retrieves the map and passes the image
           to the view.
        """
        # Get coordinate reference system and bounding box from the map
        # object in the view.
        crs = self.view.getCRS()
        bbox = self.view.getBBOX()
        # Determine the current size of the vertical section plot on the
        # screen in pixels. The image will be retrieved in this size.
        width, height = self.view.getPlotSizePx()
        # Retrieve the image.
        try:
            img, legend_img, layer, style, init_time, valid_time, level = \
                self.retrieveImage(crs=crs, bbox=bbox, width=width, height=height)
        except Exception as ex:
            logging.error("an error occurred. no image retried. (%s)" % ex)
        else:
            # Plot the image on the view canvas.
            self.view.drawImage(img)
            if style != "":
                style_title = self.get_layer_object(layer).styles[style]["title"]
            else:
                style_title = None
            tph = self.tp_height
            if tph is not None:
                tph = "{:.1f} km".format(tph)
            self.view.drawMetadata(title=self.get_layer_object(layer).title,
                                   init_time=init_time,
                                   valid_time=valid_time,
                                   level=level,
                                   style=style_title,
                                   tp=tph)
            self.view.drawLegend(legend_img)
            self.view.waypoints_interactor.update()


################################################################################

if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    app = QtGui.QApplication(sys.argv)
    win = WMSControlWidget(default_WMS=default_WMS)
    win.connect(win.btGetMap, QtCore.SIGNAL("clicked()"),
                win.getMap)
    win.show()
    sys.exit(app.exec_())





################################################################################
## IPYTHON TEST LINES.

# import wms_control; base_url = "http://localhost:8081/mss_wms"; wms = wms_control.MSSWebMapService(base_url, version='1.1.1')
# l = wms.contents["PLGeopWind"]
