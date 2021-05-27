# -*- coding: utf-8 -*-
"""

    mslib.msui.wms_control
    ~~~~~~~~~~~~~~~~~~~~~~

    Control widget to access Web Map Services.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import time
from datetime import datetime

import io
import hashlib
import logging
import mpl_toolkits.basemap as basemap
import os
import requests
import traceback
import urllib.parse
import defusedxml.ElementTree as etree
from mslib.utils import config_loader
from PyQt5 import QtCore, QtGui, QtWidgets

import mslib.ogcwms
import owslib.util
from owslib.crs import axisorder_yx
from PIL import Image, ImageOps

from mslib.msui.mss_qt import ui_wms_dockwidget as ui
from mslib.msui.mss_qt import ui_wms_password_dialog as ui_pw
from mslib.msui import wms_capabilities
from mslib.msui import constants
from mslib.utils import parse_iso_datetime, parse_iso_duration, load_settings_qsettings, save_settings_qsettings, Worker
from mslib.ogcwms import openURL, removeXMLNamespace
from mslib.msui.multilayers import Multilayers, Layer


WMS_SERVICE_CACHE = {}
WMS_URL_LIST = QtGui.QStandardItemModel()


def add_wms_urls(combo_box, url_list):
    combo_box_urls = [combo_box.itemText(_i) for _i in range(combo_box.count())]
    for url in (_url for _url in url_list if _url not in combo_box_urls):
        combo_box.addItem(url)


class MSSWebMapService(mslib.ogcwms.WebMapService):
    """Overloads the getmap() method of owslib.wms.WebMapService:

        added parameters are
         init_time
         level
         path_str

        the function times out after wms_timeout seconds.
    """

    def getmap(self, layers=None, styles=None, srs=None, bbox=None,
               format=None, size=None, time=None, init_time=None,
               path_str=None, level=None, transparent=False, bgcolor='#FFFFFF',
               time_name="time", init_time_name="init_time",
               exceptions='XML', method='Get',
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
        base_url = self.get_redirect_url(method)
        request = {'version': self.version, 'request': 'GetMap'}

        if self.version != "1.3.0":
            exceptions = "application/vnd.ogc.se_xml"

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

        request['srs' if self.version != "1.3.0" else "crs"] = str(srs)
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
        if time is not None:
            time_name = time_name if time_name == "time" else "dim_" + time_name
        if init_time is not None:
            init_time_name = "dim_" + init_time_name

        # If the parameters time and init_time are given as datetime objects,
        # create formatted strings with the given formatter. If they are
        # given as strings, use these strings directly as WMS arguments.
        if isinstance(time, datetime):
            request[time_name] = time.isoformat() + "Z"
        elif isinstance(time, str):
            request[time_name] = time

        if isinstance(init_time, datetime):
            request[init_time_name] = init_time.isoformat() + "Z"
        elif isinstance(init_time, str):
            request[init_time_name] = init_time

        if level is not None:
            request['elevation'] = str(level)

        # normalise base_url so it contains no request and no parameters
        (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(base_url)
        base_url = urllib.parse.urlunparse((scheme, netloc, path, params, "", fragment))
        request.update(dict(urllib.parse.parse_qsl(query)))
        # --(mss)

        data = urllib.parse.urlencode(request)

        # ++(mss)
        base_url = base_url.replace("ogctest.iblsoft", "ogcie.iblsoft")  # IBL Bugfix!
        base_url = base_url.replace("ogcie/obs", "ogcie.iblsoft.com/obs")  # IBL Bugfix!
        base_url = base_url.replace(", staging1", "")  # geo.beopen.eu bugfix

        complete_url = urllib.parse.urlunparse((str(""), str(""), str(base_url), str(""), data, str("")))
        if return_only_url:
            return complete_url
        logging.debug("Retrieving image from '%s'", complete_url)
        # --(mss)

        # (mss) owslib.util.openURL checks for ServiceExceptions and raises a
        # owslib.wms.ServiceException. However, openURL only checks for mime
        # types text/xml and application/xml. application/vnd.ogc.se_xml is
        # not considered. For some reason, the check below doesn't work, though..
        proxies = config_loader(dataset="proxies")

        u = openURL(base_url, data, method,
                    username=self.auth.username, password=self.auth.password, proxies=proxies)

        # check for service exceptions, and return
        # NOTE: There is little bug in owslib.util.openURL -- if the file
        # returned by the http server is an XML file, urlopen converts it
        # into an "RereadableURL" object. WHile this enables the URL content
        # to be scanned in urlopen as well as in a following method
        # (urllib2.urlopen objects only allow the content to be read once),
        # the "info" attribute is missing after the conversion..
        if hasattr(u, "info") and 'application/vnd.ogc.se_xml' in u.info()['Content-Type']:
            se_xml = u.read()
            se_tree = etree.fromstring(se_xml)
            # Remove namespaces in the response, otherwise this code might fail
            removeXMLNamespace(se_tree)
            err_message = str(se_tree.find('ServiceException').text).strip()
            raise owslib.util.ServiceException(err_message, se_xml)
        return u

    def get_redirect_url(self, method="Get"):
        # return self.getOperationByName("GetMap").methods[method]["url"]
        return self.getOperationByName("GetMap").methods[0]["url"]


class MSS_WMS_AuthenticationDialog(QtWidgets.QDialog, ui_pw.Ui_WMSAuthenticationDialog):
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
        return (self.leUsername.text(),
                self.lePassword.text())


class WMSMapFetcher(QtCore.QObject):
    """
    This class is supposed to run in a background thread to prefetch map images that may be used later on.

    This class uses code that is very similar to the actual code in the getMap call. Might be refactored
    in some way...
    """

    # start fetching next URL in queue
    process = QtCore.pyqtSignal()
    # present a final image including legend
    finished = QtCore.pyqtSignal([object, object, object, object, object, object, object])
    # triggered in case of caught exception
    exception = QtCore.pyqtSignal([Exception])
    # triggered in case of long lasting operation
    started_request = QtCore.pyqtSignal()

    def __init__(self, wms_cache, parent=None):
        super(WMSMapFetcher, self).__init__(parent)
        self.wms_cache = wms_cache
        self.maps = []
        self.map_imgs = []
        self.legend_imgs = []
        self.process.connect(self.process_map, QtCore.Qt.QueuedConnection)
        self.long_request = False

    @QtCore.pyqtSlot(list)
    def fetch_maps(self, map_list):
        """
        Initializes the list of maps to be fetched. Overwrites any remaining ones.
        Starts processing loop
        """
        self.maps = map_list
        self.process.emit()

    @QtCore.pyqtSlot()
    def process_map(self):
        """
        Processing. Self emits into event queue until list is empty. In this way,
        fetch_map events may interrupt.
        """
        if len(self.maps) == 0:
            return
        layer, kwargs, md5_filename, use_cache, legend_kwargs = self.maps[0]
        self.maps = self.maps[1:]
        self.long_request = False
        try:
            self.map_imgs.append(self.fetch_map(layer, kwargs, use_cache, md5_filename))
            self.legend_imgs.append(self.fetch_legend(use_cache=use_cache, **legend_kwargs))
        except Exception as ex:
            logging.error("MapPrefetcher Exception %s - %s.", type(ex), ex)
            # emit finished so progress dialog will be closed
            self.finished.emit(None, None, None, None, None, None, md5_filename)
            self.exception.emit(ex)
            self.map_imgs = []
            self.legend_imgs = []
        else:
            if len(self.maps) > 0:
                self.process.emit()
            else:
                self.finished.emit(
                    self.map_imgs, self.legend_imgs, kwargs["layers"][0], kwargs["styles"][0], kwargs["init_time"],
                    kwargs["time"], md5_filename)
                self.map_imgs = []
                self.legend_imgs = []

    def fetch_map(self, layer, kwargs, use_cache, md5_filename):
        """
        Retrieves a WMS map from a server or reads it from a cache if allowed
        """
        logging.debug("MapPrefetcher %s %s.", kwargs["time"], kwargs["level"])

        if use_cache and os.path.exists(md5_filename):
            if ".png" in md5_filename:
                img = Image.open(md5_filename)
                img.load()
                logging.debug("MapPrefetcher - found image cache")
            else:
                with open(md5_filename, "r") as cache:
                    return etree.fromstring(cache.read())
        else:
            self.started_request.emit()
            self.long_request = True
            urlobject = layer.get_wms().getmap(**kwargs)

            if "xml" in urlobject.info()["content-type"].lower():
                with open(md5_filename, "w") as cache:
                    cache.write(str(urlobject.read(), encoding="utf8"))
                return etree.fromstring(urlobject.read())

            image_io = io.BytesIO(urlobject.read())
            img = Image.open(image_io)
            # Check if the image is stored as indexed palette
            # with a transparent colour. Store correspondingly.
            if img.mode == "P" and "transparency" in img.info:
                img.save(md5_filename, transparency=img.info["transparency"])
            else:
                img.save(md5_filename)
            logging.debug("MapPrefetcher %s - saved filed: %s.", self, md5_filename)
        return img.convert("RGBA")

    def fetch_legend(self, urlstr=None, use_cache=True, md5_filename=None):
        """
        Retrieves a WMS legend from a server or reads it from a cache if allowed
        """
        if urlstr is None:
            return None

        if use_cache and os.path.exists(md5_filename):
            legend_img = Image.open(md5_filename)
            legend_img.load()
            logging.debug("MapPrefetcher - found legend cache")
        else:
            if not self.long_request:
                self.started_request.emit()
                self.long_request = True
            # This StringIO object can then be passed as a file substitute to
            # Image.open(). See
            #    http://www.pythonware.com/library/pil/handbook/image.htm
            logging.debug("Retrieving legend from '%s'", urlstr)
            urlobject = requests.get(urlstr)
            image_io = io.BytesIO(urlobject.content)
            try:
                legend_img_raw = Image.open(image_io)
            except Exception as ex:
                # This exception may be triggered if there was a problem with the legend
                # as present with http://geoservices.knmi.nl/cgi-bin/HARM_N25.cgi
                # it is deemed preferential to display the WMS map and forget about the
                # legend than not displaying anything.
                logging.error("Wildecard Exception %s - %s.", type(ex), ex)
                return None
            legend_img = legend_img_raw.crop(legend_img_raw.getbbox())
            # Store the retrieved image in the cache, if enabled.
            try:
                legend_img.save(md5_filename, transparency=0)
            except Exception as ex:
                logging.debug("Wildecard Exception %s - %s.", type(ex), ex)
                legend_img.save(md5_filename)
        return legend_img.convert("RGBA")


class WMSControlWidget(QtWidgets.QWidget, ui.Ui_WMSDockWidget):
    """The base class of the WMS control widget: Provides the GUI
       elements and common functionality to access a WMS. This class
       is not instantiated directly, see HSecWMSControlWidget and
       VSecWMSControlWidget below.

    NOTE: Currently this class can only handle WMS 1.1.1/1.3.0 servers.
    """

    prefetch = QtCore.pyqtSignal([list], name="prefetch")
    fetch = QtCore.pyqtSignal([list], name="fetch")
    signal_disable_cbs = QtCore.Signal(name="disable_cbs")
    signal_enable_cbs = QtCore.Signal(name="enable_cbs")
    image_displayed = QtCore.pyqtSignal()

    def __init__(self, parent=None, default_WMS=None, wms_cache=None, view=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        default_WMS -- list of strings that specify WMS URLs that will be
                       displayed in the URL combobox as default values.
        """
        super(WMSControlWidget, self).__init__(parent)
        self.setupUi(self)

        self.view = view

        # Multilayering things
        self.multilayers = Multilayers(self)
        self.pbLayerSelect.clicked.connect(lambda: (self.multilayers.hide(), self.multilayers.show()))
        self.multilayers.cbWMS_URL.editTextChanged.connect(
            lambda text: self.multilayers.pbViewCapabilities.setEnabled(text in self.multilayers.layers))

        # Initial list of WMS servers.
        self.multilayers.cbWMS_URL.setModel(WMS_URL_LIST)
        if default_WMS is not None:
            add_wms_urls(self.multilayers.cbWMS_URL, default_WMS)
        # set last connected url to editable
        wms_settings = load_settings_qsettings('wms', {'recent_wms_url': None})
        if wms_settings['recent_wms_url'] is not None:
            add_wms_urls(self.multilayers.cbWMS_URL, [wms_settings['recent_wms_url']])

        self.layerChangeInProgress = False
        self.save_level = None

        # Initialise GUI elements that control WMS parameters.
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

        self.enable_level_elements(False)
        self.enable_valid_time_elements(False)
        self.enable_init_time_elements(False)
        self.btGetMap.setEnabled(False)
        self.multilayers.pbViewCapabilities.setEnabled(False)

        self.cbTransparent.setChecked(False)

        # Check for WMS image cache directory, create if necessary.
        if wms_cache is not None:
            self.wms_cache = os.path.join(wms_cache, "")
            logging.debug("checking for WMS image cache at %s ...", self.wms_cache)
            if not os.path.exists(self.wms_cache):
                logging.debug("  created new image cache directory.")
                os.makedirs(self.wms_cache)
            else:
                logging.debug("  found.")
            # Service the cache (delete files that are too old, remove oldest
            # files if cache is too large).
            self.service_cache()
        else:
            self.wms_cache = None

        # Initialise date/time fields with current day, 00 UTC.
        self.dteInitTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)))
        self.dteValidTime.setDateTime(QtCore.QDateTime(
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)))

        # Connect slots and signals.
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.multilayers.btGetCapabilities.clicked.connect(self.get_capabilities)
        self.multilayers.pbViewCapabilities.clicked.connect(self.view_capabilities)

        self.btClearMap.clicked.connect(self.clear_map)

        self.cbLevel.currentIndexChanged.connect(self.level_changed)
        self.cbInitTime.currentIndexChanged.connect(self.init_time_changed)
        self.cbValidTime.currentIndexChanged.connect(self.valid_time_changed)
        self.multilayers.needs_repopulate.connect(self.populate_ui)

        self.tbInitTime_back.clicked.connect(self.init_time_back_click)
        self.tbInitTime_fwd.clicked.connect(self.init_time_fwd_click)
        self.tbInitTime_cbback.clicked.connect(self.cb_init_time_back_click)
        self.tbInitTime_cbfwd.clicked.connect(self.cb_init_time_fwd_click)
        self.dteInitTime.dateTimeChanged.connect(self.check_init_time)
        self.tbValidTime_back.clicked.connect(self.valid_time_back_click)
        self.tbValidTime_fwd.clicked.connect(self.valid_time_fwd_click)
        self.tbValidTime_cbback.clicked.connect(self.cb_valid_time_back_click)
        self.tbValidTime_cbfwd.clicked.connect(self.cb_valid_time_fwd_click)
        self.dteValidTime.dateTimeChanged.connect(self.check_valid_time)
        self.tbLevel_back.clicked.connect(self.level_back_click)
        self.tbLevel_fwd.clicked.connect(self.level_fwd_click)

        self.btClearCache.clicked.connect(self.clearCache)
        self.multilayers.cbWMS_URL.editTextChanged.connect(self.wms_url_changed)
        if view is not None and hasattr(view, "redrawn"):
            self.view.redrawn.connect(self.after_redraw)

        # Progress dialog to inform the user about image ongoing retrievals.
        self.pdlg = QtWidgets.QProgressDialog(
            "retrieving image...", "Cancel", 0, 10, parent=self.parent())
        self.pdlg.close()

        # Progress dialog to inform the user about ongoing capability requests.
        self.capabilities_worker = Worker(None)
        self.cpdlg = QtWidgets.QProgressDialog(
            "retrieving wms capabilities...", "Cancel", 0, 10, parent=self.multilayers)
        self.cpdlg.canceled.connect(self.stop_capabilities_retrieval)
        self.cpdlg.close()

        self.thread_prefetch = QtCore.QThread()  # no parent!
        self.thread_prefetch.start()
        self.thread_fetch = QtCore.QThread()  # no parent!
        self.thread_fetch.start()

        self.prefetcher = None
        self.fetcher = None
        self.expected_img = None
        self.check_for_allowed_crs = True

        if self.multilayers.cbWMS_URL.count() > 0:
            self.multilayers.cbWMS_URL.setCurrentIndex(0)
            self.wms_url_changed(self.multilayers.cbWMS_URL.currentText())

    def __del__(self):
        """Destructor.
        """
        # Service the WMS cache on application exit.
        if self.wms_cache is not None:
            self.service_cache()
        # properly terminate background threads. wait is necessary!
        self.thread_prefetch.quit()
        self.thread_prefetch.wait()
        self.thread_fetch.quit()
        self.thread_fetch.wait()

    def get_all_maps(self, disregard_current=False):
        if self.multilayers.cbMultilayering.isChecked():
            self.get_map(self.multilayers.get_active_layers())
        else:
            self.get_map([self.multilayers.get_current_layer()])

    def initialise_wms(self, base_url, version="1.3.0"):
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
        # initialize login cache fomr config file, but do not overwrite existing keys
        for key, value in config_loader(dataset="WMS_login").items():
            if key not in constants.WMS_LOGIN_CACHE:
                constants.WMS_LOGIN_CACHE[key] = value
        username, password = constants.WMS_LOGIN_CACHE.get(base_url, (None, None))

        def on_success(wms):
            self.cpdlg.setValue(9)
            if wms is not None:

                # update the combo box, if entry requires change/insertion
                found = False
                current_url = self.multilayers.cbWMS_URL.currentText()
                for count in range(self.multilayers.cbWMS_URL.count()):
                    if self.multilayers.cbWMS_URL.itemText(count) == current_url:
                        self.multilayers.cbWMS_URL.setItemText(count, base_url)
                        self.multilayers.cbWMS_URL.setCurrentIndex(count)
                        found = True
                        break
                    if self.multilayers.cbWMS_URL.itemText(count) == base_url:
                        self.multilayers.cbWMS_URL.setCurrentIndex(count)
                        found = True
                if not found:
                    logging.debug("inserting URL: %s", base_url)
                    add_wms_urls(self.multilayers.cbWMS_URL, [base_url])
                    self.multilayers.cbWMS_URL.setEditText(base_url)
                    save_settings_qsettings('wms', {'recent_wms_url': base_url})

                self.activate_wms(wms)
                WMS_SERVICE_CACHE[wms.url] = wms
                self.cpdlg.close()

        def on_failure(e):
            try:
                raise e
            except owslib.util.ServiceException as ex:
                logging.error("ERROR: %s %s", type(ex), ex)
                if str(ex).startswith("401") or str(ex).find("Error 401") >= 0 or str(ex).find(
                        "Unauthorized") >= 0:
                    # Catch the "401 Unauthorized" error if one has been
                    # returned by the server and ask the user for username
                    # and password.
                    # WORKAROUND (mr, 28Mar2013) -- owslib doesn't recognize
                    # the Apache 401 messages, we get an XML message here but
                    # no error code. Quick workaround: Scan the XML message for
                    # the string "Error 401"...
                    dlg = MSS_WMS_AuthenticationDialog(parent=self.multilayers)
                    dlg.setModal(True)
                    if dlg.exec_() == QtWidgets.QDialog.Accepted:
                        username, password = dlg.getAuthInfo()
                        # If user & pw have been entered, cache them.
                        constants.WMS_LOGIN_CACHE[base_url] = (username, password)
                        self.capabilities_worker.function = lambda: MSSWebMapService(
                            base_url, version=version,
                            username=username, password=password)
                        self.capabilities_worker.start()
                    else:
                        self.cpdlg.close()
                        return
                else:
                    logging.error("cannot load capabilities document.. "
                                  "no layers can be used in this view.")
                    QtWidgets.QMessageBox.critical(
                        self.multilayers, self.tr("Web Map Service"),
                        self.tr(f"ERROR: We cannot load the capability document!\n\n{type(ex)}\n{ex}"))
                    self.cpdlg.close()
            except Exception as ex:
                logging.error("cannot load capabilities document.. "
                              "no layers can be used in this view.")
                QtWidgets.QMessageBox.critical(
                    self.multilayers, self.tr("Web Map Service"),
                    self.tr(f"ERROR: We cannot load the capability document!\n\n{type(ex)}\n{ex}"))
                self.cpdlg.close()

        try:
            str(base_url)
        except UnicodeEncodeError:
            logging.error("got a unicode url?!: '%s'", base_url)
            QtWidgets.QMessageBox.critical(self.multilayers, self.tr("Web Map Service"),
                                           self.tr("ERROR: We cannot parse unicode URLs!"))
            self.cpdlg.close()

        self.capabilities_worker = Worker.create(lambda: MSSWebMapService(base_url, version=version,
                                                                          username=username, password=password),
                                                 on_success, on_failure)

    def wms_url_changed(self, text):
        wms = WMS_SERVICE_CACHE.get(text)
        if wms is not None:
            self.activate_wms(wms, cache=True)

    @QtCore.pyqtSlot(Exception)
    def display_exception(self, ex):
        logging.error("ERROR: %s %s", type(ex), ex)
        logging.debug("%s", traceback.format_exc())
        QtWidgets.QMessageBox.critical(
            self, self.tr("Web Map Service"), self.tr(f"ERROR:\n{type(ex)}\n{ex}"))

    @QtCore.pyqtSlot()
    def display_progress_dialog(self):
        logging.debug("showing progress dialog")
        self.pdlg.reset()
        self.pdlg.setValue(5)
        self.pdlg.setModal(True)
        self.pdlg.show()

    def display_capabilities_dialog(self):
        logging.debug("showing capabilities dialog")
        self.cpdlg.reset()
        self.cpdlg.setValue(1)
        self.cpdlg.setModal(True)
        self.cpdlg.show()

    def stop_capabilities_retrieval(self):
        logging.debug("stopping capabilities retrieval")
        try:
            self.capabilities_worker.quit()
            self.capabilities_worker.disconnect()
        except TypeError:
            pass

    def clear_map(self):
        logging.debug("clear figure")
        self.view.clear_figure()
        logging.debug("enabling checkboxes in map-options if any")
        self.signal_enable_cbs.emit()

    def get_capabilities(self):
        """
        Query the WMS server in the URL combobox for its capabilities.
        """

        # Load new WMS. Only add those layers to the combobox that can provide
        # the CRS that match the filter of this module.
        base_url = self.multilayers.cbWMS_URL.currentText()
        params = {'service': 'WMS',
                  'request': 'GetCapabilities'}

        def on_success(request):
            self.cpdlg.setValue(5)
            # url shortener url translated
            url = request.url

            url = url.replace("?service=WMS", "").replace("&service=WMS", "") \
                .replace("?request=GetCapabilities", "").replace("&request=GetCapabilities", "")
            logging.debug("requesting capabilities from %s", url)
            self.initialise_wms(url, None)

        def on_failure(e):
            try:
                raise e
            except (requests.exceptions.TooManyRedirects,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.InvalidURL,
                    requests.exceptions.InvalidSchema,
                    requests.exceptions.MissingSchema) as ex:
                logging.error("Cannot load capabilities document.\n"
                              "No layers can be used in this view.")
                QtWidgets.QMessageBox.critical(
                    self.multilayers, self.tr("Web Map Service"),
                    self.tr(f"ERROR: We cannot load the capability document!\n\\n{type(ex)}\n{ex}"))
            finally:
                self.cpdlg.close()

        self.display_capabilities_dialog()
        self.capabilities_worker = Worker.create(lambda: requests.get(base_url, params=params),
                                                 on_success, on_failure)

    def activate_wms(self, wms, cache=False):
        # Parse layer tree of the wms object and discover usable layers.
        stack = list(wms.contents.values())
        filtered_layers = set()
        while len(stack) > 0:
            layer = stack.pop()
            if len(layer.layers) > 0:
                stack.extend(layer.layers)
            elif self.is_layer_aligned(layer):
                cb_string = f"{layer.title} | {layer.name}"
                filtered_layers.add(cb_string)
        logging.debug("discovered %i layers that can be used in this view",
                      len(filtered_layers))
        filtered_layers = sorted(filtered_layers)
        if not cache and wms.url in self.multilayers.layers and \
                wms.capabilities_document.decode("utf-8") != \
                self.multilayers.layers[wms.url]["wms"].capabilities_document.decode("utf-8"):
            self.multilayers.delete_server(self.multilayers.layers[wms.url]["header"])
        self.multilayers.add_wms(wms)
        for layer in filtered_layers:
            self.multilayers.add_multilayer(layer, wms)
        self.multilayers.filter_multilayers()
        self.multilayers.update_checkboxes()
        self.multilayers.pbViewCapabilities.setEnabled(True)
        if len(filtered_layers) > 0:
            self.populate_ui()

        if self.prefetcher is not None:
            self.prefetch.disconnect(self.prefetcher.fetch_maps)
        if self.fetcher is not None:
            self.fetch.disconnect(self.fetcher.fetch_maps)

        self.prefetcher = WMSMapFetcher(self.wms_cache)
        self.prefetcher.moveToThread(self.thread_prefetch)
        self.prefetch.connect(self.prefetcher.fetch_maps)  # implicitely uses a queued connection

        self.fetcher = WMSMapFetcher(self.wms_cache)
        self.fetcher.moveToThread(self.thread_fetch)
        self.fetch.connect(self.fetcher.fetch_maps)  # implicitely uses a queued connection
        self.fetcher.finished.connect(self.continue_retrieve_image)  # implicitely uses a queued connection
        self.fetcher.exception.connect(self.display_exception)  # implicitely uses a queued connection
        self.fetcher.started_request.connect(self.display_progress_dialog)  # implicitely uses a queued connection

        # logic to disable fill continents, fill oceans on connection to
        self.signal_disable_cbs.emit()

    def view_capabilities(self):
        """Open a WMSCapabilitiesBrowser dialog showing the capabilities
           document.
        """
        logging.debug("Opening WMS capabilities browser..")
        wms = self.multilayers.layers[self.multilayers.cbWMS_URL.currentText()]["wms"]
        if wms is not None:
            wmsbrws = wms_capabilities.WMSCapabilitiesBrowser(
                parent=self.multilayers,
                url=wms.url,
                capabilities=wms)
            wmsbrws.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            wmsbrws.show()

    def get_layer_object(self, wms, layername):
        """Returns the object from the layer tree that fits the given
           layer name.
        """
        if wms is None:
            return None
        if layername in wms.contents:
            return wms.contents[layername]
        else:
            stack = list(wms.contents.values())
            while len(stack) > 0:
                layer = stack.pop()
                if layer.name == layername:
                    return layer
                if len(layer.layers) > 0:
                    stack.extend(layer.layers)
        return None

    def parse_time_extent(self, values):
        times = []
        for time_item in [i.strip() for i in values]:
            try:
                list_desc = time_item.split("/")

                if len(list_desc) == 3:
                    time_val = parse_iso_datetime(list_desc[0])
                    if "current" in list_desc[1]:
                        end_time = datetime.utcnow()
                    else:
                        end_time = parse_iso_datetime(list_desc[1])
                    delta = parse_iso_duration(list_desc[2])
                    while time_val <= end_time:
                        times.append(time_val)
                        time_val += delta

                elif len(list_desc) == 1:
                    times.append(parse_iso_datetime(time_item))
                else:
                    raise ValueError("value has incorrect number of entries.")

            except Exception as ex:
                logging.debug("Wildcard Exception %s - %s.", type(ex), ex)
                logging.error("Can't understand time string '%s'. Please check the implementation.", time_item)
        return times

    def disable_ui(self):
        self.disable_cbInitTime_elements()
        self.disable_cbValidTime_elements()
        self.disable_dteInitTime_elements()
        self.disable_dteValidTime_elements()
        self.enable_valid_time_elements(False)
        self.enable_init_time_elements(False)
        self.enable_level_elements(False)
        self.btGetMap.setEnabled(False)

    def populate_ui(self):
        """
        Adds the values of the current layer to the UI comboboxes
        """
        self.layerChangeInProgress = True
        self.cbLevel.clear()
        self.cbInitTime.clear()
        self.cbValidTime.clear()

        active_layers = self.multilayers.get_active_layers()
        layer = self.multilayers.get_current_layer()

        if not layer:
            self.lLayerName.setText("No Layer selected")
            self.disable_ui()
            return

        else:
            self.btGetMap.setEnabled(True)

        self.lLayerName.setText(str(layer))

        tooltip_text = ""
        for active_layer in active_layers if layer.checkState(0) else [layer]:
            tooltip_text += f"{active_layer}\n"
        self.lLayerName.setToolTip(tooltip_text.strip())

        if len(active_layers) > 1 and layer.checkState(0):
            self.lLayerName.setText(self.lLayerName.text() + f" (and {len(active_layers) - 1} more)")

        crs = layer.get_allowed_crs()
        levels, itimes, vtimes = layer.get_levels(), layer.get_itimes(), layer.get_vtimes()
        if vtimes and itimes:
            vtimes = vtimes[next((i for i, vtime in enumerate(vtimes) if vtime >= layer.get_itime()), 0):]

        if levels:
            self.cbLevel.addItems(levels)
            self.cbLevel.setCurrentIndex(self.cbLevel.findText(layer.get_level()))
        self.enable_level_elements(len(levels) > 0)

        if itimes:
            self.cbInitTime.addItems(itimes)
            self.cbInitTime.setCurrentIndex(self.cbInitTime.findText(layer.get_itime()))
        self.enable_init_time_elements(len(itimes) > 0)

        if vtimes:
            self.cbValidTime.addItems(vtimes)
            self.cbValidTime.setCurrentIndex(self.cbValidTime.findText(layer.get_vtime()))
        self.enable_valid_time_elements(len(vtimes) > 0)

        if not self.init_time_changed():
            self.disable_dteInitTime_elements()
        if not self.valid_time_changed():
            self.disable_dteValidTime_elements()
        if self.cbInitTime.count() == 0:
            self.disable_cbInitTime_elements()
        if self.cbValidTime.count() == 0:
            self.disable_cbValidTime_elements()

        if crs and \
           self.parent() is not None and \
           self.parent().parent() is not None:
            logging.debug("Layer offers '%s' projections.", crs)
            extra = [_code for _code in crs if _code.startswith("EPSG")]
            extra = [_code for _code in sorted(extra) if _code[5:] in basemap.epsg_dict]
            logging.debug("Selected '%s' for Combobox.", extra)
            self.parent().parent().update_predefined_maps(extra)

        self.layerChangeInProgress = False

    @staticmethod
    def secs_from_timestep(timestep_string):
        """Convert a string specifying a time step (e.g. 5 min, 3 hours) to
           seconds.

        Allowed formats:
         a) 'XX min', where XX is an integer.
         b) 'XX hours', where XX is an integer.
         c) 'XX days', where XX is an integer.
        """
        try:
            return 60 * int(timestep_string.split(" min")[0])
        except ValueError as error:
            logging.debug("ValueError Exception %s", error)
        try:
            return 3600 * int(timestep_string.split(" hour")[0])
        except ValueError as error:
            logging.debug("ValueError Exception %s", error)
        try:
            return 86400 * int(timestep_string.split(" days")[0])
        except ValueError as error:
            logging.debug("ValueError Exception %s", error)
            raise ValueError(f"cannot convert '{timestep_string}' to seconds: wrong format.")

    def init_time_back_click(self):
        """Slot for the tbInitTime_back button.
        """
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteInitTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(self.cbInitTime_step.currentText())
        self.dteInitTime.setDateTime(d.addSecs(-1. * secs))
        self.auto_update()

    def init_time_fwd_click(self):
        """Slot for the tbInitTime_fwd button.
        """
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteInitTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(self.cbInitTime_step.currentText())
        self.dteInitTime.setDateTime(d.addSecs(secs))
        self.auto_update()

    def valid_time_back_click(self):
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteValidTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(self.cbValidTime_step.currentText())
        self.dteValidTime.setDateTime(d.addSecs(-1. * secs))
        self.auto_update()

    def valid_time_fwd_click(self):
        # Get QDateTime object from QtDateTimeEdit field.
        d = self.dteValidTime.dateTime()
        # Add value from cbInitTime_step and set new date.
        secs = self.secs_from_timestep(self.cbValidTime_step.currentText())
        self.dteValidTime.setDateTime(d.addSecs(secs))
        self.auto_update()

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
        self.init_time_changed()

    def cb_init_time_fwd_click(self):
        ci = self.cbInitTime.currentIndex()
        if ci < self.cbInitTime.count() - 1:
            ci = ci + 1
        self.cbInitTime.setCurrentIndex(ci)
        self.init_time_changed()

    def cb_valid_time_back_click(self):
        ci = self.cbValidTime.currentIndex()
        if ci > 0:
            ci = ci - 1
        self.cbValidTime.setCurrentIndex(ci)
        self.valid_time_changed()

    def cb_valid_time_fwd_click(self):
        ci = self.cbValidTime.currentIndex()
        if ci < self.cbValidTime.count() - 1:
            ci = ci + 1
        self.cbValidTime.setCurrentIndex(ci)
        self.valid_time_changed()

    def auto_update(self):
        """If the auto update check box is checked, let btGetMap emit a
           clicked() signal everytime this method is called.
           autoUpdate() should be called from the slots that handle
           time and level changes.

        If the the layerChangeInProgress flag is set no update will be
        performed (lock mechanism to prevent erroneous requests during
        a layer change).
        """
        if self.btGetMap.isEnabled() and self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
            self.get_all_maps()

    def check_init_time(self, dt):
        """Checks whether an initialisation time set with the init time
           date/time edit is contained in the list of init times advertised
           by the WMS server.

        If the time is not contained in the list, the font will be set to
        'strike through' to indicate an invalid time.
        """
        font = self.dteInitTime.font()
        pydt = dt.toPyDateTime()
        init_time_available = pydt in self.multilayers.get_current_layer().allowed_init_times
        font.setStrikeOut(not init_time_available)
        self.dteInitTime.setFont(font)
        if init_time_available:
            index = self.cbInitTime.findText(pydt.isoformat() + "Z")
            self.cbInitTime.setCurrentIndex(index)

    def check_valid_time(self, dt):
        """Same as check_init_time, but for valid time.
        """
        valid_time_available = True
        pydt = dt.toPyDateTime()
        if self.multilayers.get_current_layer().allowed_valid_times:
            if pydt in self.multilayers.get_current_layer().allowed_valid_times:
                index = self.cbValidTime.findText(pydt.isoformat() + "Z")
                # setCurrentIndex also sets the date/time edit via signal.
                if index > -1:
                    self.cbValidTime.setCurrentIndex(index)
                else:
                    valid_time_available = False
            else:
                valid_time_available = False
        font = self.dteValidTime.font()
        font.setStrikeOut(not valid_time_available)
        self.dteValidTime.setFont(font)

    def init_time_changed(self):
        """Slot to be called when the current index of the init time
           combo box is changed. The method tries to sync to the
           init time date/time edit.
        """
        init_time = self.cbInitTime.currentText()
        if init_time != "":
            init_time = parse_iso_datetime(init_time)
            if init_time is not None:
                self.dteInitTime.setDateTime(init_time)

        if self.multilayers.threads == 0 and not self.layerChangeInProgress:
            self.multilayers.get_current_layer().set_itime(self.cbInitTime.currentText())
            self.multilayers.carry_parameters["itime"] = self.cbInitTime.currentText()

        self.auto_update()
        return init_time == "" or init_time is not None

    def valid_time_changed(self):
        """Same as initTimeChanged(), but for the valid time elements.
        """
        valid_time = self.cbValidTime.currentText()
        if valid_time != "":
            valid_time = parse_iso_datetime(valid_time)
            if valid_time is not None:
                self.dteValidTime.setDateTime(valid_time)

        if self.multilayers.threads == 0 and not self.layerChangeInProgress:
            self.multilayers.get_current_layer().set_vtime(self.cbValidTime.currentText())
            self.multilayers.carry_parameters["vtime"] = self.cbValidTime.currentText()

        self.auto_update()
        return valid_time == "" or valid_time is not None

    def level_changed(self):
        if self.multilayers.threads == 0 and not self.layerChangeInProgress:
            self.multilayers.get_current_layer().set_level(self.cbLevel.currentText())
            self.multilayers.carry_parameters["level"] = self.cbLevel.currentText()
        self.auto_update()

    def enable_level_elements(self, enable):
        """Enable or disable the GUI elements allowing vertical elevation
           level control.
        """
        self.cbLevel.setEnabled(enable and self.cbLevel.count() > 1)
        self.tbLevel_back.setEnabled(enable)
        self.tbLevel_fwd.setEnabled(enable)

    def enable_init_time_elements(self, enable):
        """Enables or disables the GUI elements allowing initialisation time
           control.
        """
        self.cbInitTime.setEnabled(enable)
        self.dteInitTime.setEnabled(enable)
        self.tbInitTime_back.setEnabled(enable)
        self.tbInitTime_fwd.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)
        self.cbInitTime_step.setEnabled(enable)

    def enable_valid_time_elements(self, enable):
        """Enables or disables the GUI elements allowing valid time
           control.
        """
        self.cbValidTime.setEnabled(enable)
        self.dteValidTime.setEnabled(enable)
        self.tbValidTime_back.setEnabled(enable)
        self.tbValidTime_fwd.setEnabled(enable)
        self.tbValidTime_cbback.setEnabled(enable)
        self.tbValidTime_cbfwd.setEnabled(enable)
        self.cbValidTime_step.setEnabled(enable)

    def disable_dteInitTime_elements(self):
        """Disables init time date/time edit elements.
        """
        enable = False
        self.dteInitTime.setEnabled(enable)
        self.tbInitTime_back.setEnabled(enable)
        self.tbInitTime_fwd.setEnabled(enable)
        self.cbInitTime_step.setEnabled(enable)

    def disable_dteValidTime_elements(self):
        """Disables valid time date/time edit elements.
        """
        enable = False
        self.dteValidTime.setEnabled(enable)
        self.tbValidTime_back.setEnabled(enable)
        self.tbValidTime_fwd.setEnabled(enable)
        self.cbValidTime_step.setEnabled(enable)

    def disable_cbInitTime_elements(self):
        """Disables init time combobox elements.
        """
        enable = False
        self.cbInitTime.setEnabled(enable)
        self.tbInitTime_cbback.setEnabled(enable)
        self.tbInitTime_cbfwd.setEnabled(enable)

    def disable_cbValidTime_elements(self):
        """Disables valid time combobox elements.
        """
        enable = False
        self.cbValidTime.setEnabled(enable)
        self.tbValidTime_cbback.setEnabled(enable)
        self.tbValidTime_cbfwd.setEnabled(enable)

    def get_layer(self):
        return self.multilayers.get_current_layer().get_layer()

    def get_style(self):
        return self.multilayers.get_current_layer().get_style()

    def get_level(self):
        return self.multilayers.get_current_layer().get_level_name()

    def get_init_time(self):
        """Get the initialisation time from the GUI elements.

        If the init time date/time edit is enabled (i.e. the times specified
        in the WMS capabilities document can be interpreted), return a
        datetime object of the currently set time. Otherwise, return the
        string that is selected in the init time combobox.
        """
        if self.cbInitialisationOn.isChecked():
            if self.dteInitTime.isEnabled():
                return self.dteInitTime.dateTime().toPyDateTime()
            else:
                itime_str = self.multilayers.get_current_layer().get_itime()
                return itime_str
        else:
            return None

    def get_valid_time(self):
        """The same as getInitTime(), but for the valid time.
        """
        if self.cbValidOn.isChecked():
            if self.dteValidTime.isEnabled():
                return self.dteValidTime.dateTime().toPyDateTime()
            else:
                vtime_str = self.multilayers.get_current_layer().get_vtime()
                return vtime_str
        else:
            return None

    def caching_enabled(self):
        """Returns if the image cache is enabled.
        """
        return self.wms_cache is not None and self.cbCacheEnabled.isChecked()

    def get_md5_filename(self, layer, kwargs):
        urlstr = layer.get_wms().getmap(return_only_url=True, **kwargs)
        ending = ".png" if "image" in kwargs["format"] else ".xml"
        return os.path.join(self.wms_cache, hashlib.md5(urlstr.encode('utf-8')).hexdigest() + ending)

    def retrieve_image(self, layers=None, crs="EPSG:4326", bbox=None, path_string=None,
                       width=800, height=400, transparent=False, format="image/png"):
        """Retrieve an image of the layer currently selected in the
           GUI elements from the current WMS provider. If caching is
           enabled, first check the cache for the requested image. If
           the image is retrieved from the WMS and caching is enabled,
           store the image into the cache.
           If a legend graphic is available for the layer, this image
           is also retrieved.
        Arguments:
        crs -- coordinate reference: system as a string passed to the WMS
        path_string -- string of waypoints that resemble a vertical
                       section path. Can be omitted for horizontal
                       sections.
        bbox -- bounding box as list of four floats
        width, height -- width and height of requested image in pixels
        """
        # Get layer and style names.
        if not layers:
            layers = [self.multilayers.get_current_layer()]
        if isinstance(layers, Layer):
            layers = [layers]

        layer = layers[0]

        layer_name = [layer.get_layer() for layer in layers]
        style = [layer.get_style() if "image" in format else "" for layer in layers]
        level = layer.get_level_name()

        def normalize_crs(crs):
            if any(crs.startswith(_prefix) for _prefix in ("MSS", "AUTO")):
                return crs.split(",")[0]
            return crs

        if self.check_for_allowed_crs and normalize_crs(crs) not in layer.allowed_crs:
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr("Web Map Service"),
                self.tr(f"WARNING: Selected CRS '{crs}' not contained in allowed list of supported CRS for this WMS\n"
                        f"({layer.allowed_crs})\n"
                        "Continue ?"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Ignore | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.Ignore:
                self.check_for_allowed_crs = False
            elif ret == QtWidgets.QMessageBox.No:
                return

        # get...Time() will return None if the corresponding checkboxes are
        # disabled. <None> objects passed to wms.getmap will not be included
        # in the query URL that is send to the server.
        init_time = layer.get_itime()
        valid_time = layer.get_vtime()

        logging.debug("fetching layer '%s'; style '%s', width %d, height %d",
                      layer, style, width, height)
        logging.debug("crs=%s, path=%s", crs, path_string)
        logging.debug("init_time=%s, valid_time=%s", init_time, valid_time)
        logging.debug("level=%s", level)
        logging.debug("transparent=%s", transparent)

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
            kwargs = {"layers": layer_name,
                      "styles": style,
                      "srs": crs,
                      "bbox": bbox,
                      "path_str": path_string,
                      "time": valid_time,
                      "init_time": init_time,
                      "level": level,
                      "time_name": layer.vtime_name,
                      "init_time_name": layer.itime_name,
                      "size": (width, height),
                      "format": format,
                      "transparent": transparent}
            legend_kwargs = {"urlstr": layer.get_legend_url(), "md5_filename": None}
            if legend_kwargs["urlstr"] is not None:
                legend_kwargs["md5_filename"] = os.path.join(
                    self.wms_cache, hashlib.md5(legend_kwargs["urlstr"].encode('utf-8')).hexdigest() + ".png")

            # If caching is enabled, get the URL and check the image cache
            # directory for the suitable image file.
            if self.caching_enabled():
                prefetch_config = config_loader(dataset="wms_prefetch")
                prefetch_entries = ["validtime_fwd", "validtime_bck", "level_up", "level_down"]
                for _x in prefetch_entries:
                    if _x in prefetch_config:
                        try:
                            value = int(prefetch_config[_x])
                        except ValueError as ex:
                            logging.error("ERROR: %s %s", type(ex), ex)
                            value = 0
                        prefetch_config[_x] = max(0, value)
                    else:
                        prefetch_config[_x] = 0
                fetch_nr = sum([prefetch_config[_x] for _x in prefetch_entries])
                if fetch_nr > 0:
                    pre_tfwd, pre_tbck, pre_lfwd, pre_lbck = [prefetch_config[_x] for _x in prefetch_entries]
                    ci_time, ci_level = self.cbValidTime.currentIndex(), self.cbLevel.currentIndex()
                    prefetch_key_values = \
                        [("time", self.cbValidTime.itemText(ci_p))
                         for ci_p in list(range(ci_time + 1, ci_time + 1 + pre_tfwd)) +
                            list(range(ci_time - pre_tbck, ci_time))
                         if 0 <= ci_p < self.cbValidTime.count()] + \
                        [("level", self.cbLevel.itemText(ci_p).split(" (")[0])
                         for ci_p in range(ci_level - pre_lbck, ci_level + 1 + pre_lfwd)
                         if ci_p != ci_level and 0 <= ci_p < self.cbLevel.count()]
                    prefetch_maps = []
                    for key, value in prefetch_key_values:
                        kwargs_new = kwargs.copy()
                        kwargs_new[key] = value
                        prefetch_maps.append((layer, kwargs_new, self.get_md5_filename(layer, kwargs_new), True, {}))
                    self.prefetch.emit(prefetch_maps)

            md5_filename = self.get_md5_filename(layer, kwargs)
            self.expected_img = md5_filename
            self.pdlg.reset()
            return [(layer, kwargs, md5_filename, self.caching_enabled(), legend_kwargs)]

        except Exception as ex:
            self.display_exception(ex)

    @QtCore.pyqtSlot(object, object, object, object, object, object, object)
    def continue_retrieve_image(self, img, legend_img, layer, style, init_time, valid_time, md5_filename):
        if self.pdlg.wasCanceled() or self.expected_img != md5_filename:
            return
        self.pdlg.close()
        if img is None:
            return

        complete_level = self.cbLevel.currentText()
        complete_level = complete_level if complete_level != "" else None
        self.display_retrieved_image(img, legend_img, layer, style, init_time, valid_time, complete_level)
        # this is for cases where 'remove' button is clicked, then 'retrieve' is clicked
        self.signal_disable_cbs.emit()
        self.image_displayed.emit()

    def get_map(self, layers=None):
        """Prototypical stub for getMap() function. Needs to be reimplemented
           in derived classes.
        """
        logging.error("getMap not implemented in base class.")

    def after_redraw(self):
        """Event handler that a canvas can call after it has been redrawn.
        """
        self.auto_update()

    def clearCache(self):
        """Clear the image file cache. First ask the user for confirmation.
        """
        # User confirmation to clear the cache.
        clear = (QtWidgets.QMessageBox.question(
            self, "Clear Cache",
            "Do you really want to clear the cache? All stored image "
            "files will be deleted.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes)
        if clear:
            # Delete all files in cache.
            if self.wms_cache is not None:
                cached_files = os.listdir(self.wms_cache)
                logging.debug("clearing cache; deleting %i files...", len(cached_files))
                try:
                    for f in cached_files:
                        os.remove(os.path.join(self.wms_cache, f))
                except (IOError, OSError) as ex:
                    msg = f"ERROR: Cannot delete file '{f}'. ({type(ex)}: {ex})"
                    logging.error(msg)
                    QtWidgets.QMessageBox.critical(self, self.tr("Web Map Service"), self.tr(msg))
                else:
                    logging.debug("cache has been cleared.")
            else:
                logging.debug("no cache exists that can be cleared.")

    def service_cache(self):
        """Service the cache: Remove all files older than the maximum file
           age specified in mss_settings, and remove the oldest files if the
           maximum cache size has been reached.
        """
        logging.debug("servicing cache...")

        # Create a list of all files in the cache.
        files = [os.path.join(self.wms_cache, f) for f in os.listdir(self.wms_cache)]
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
        try:
            for f, fsize, fage in files:
                cum_size_bytes += fsize
                if (cum_size_bytes > config_loader(dataset="wms_cache_max_size_bytes") or
                        fage > config_loader(dataset="wms_cache_max_age_seconds")):
                    os.remove(f)
                    removed_files += 1
        except (IOError, OSError) as ex:
            msg = f"ERROR: Cannot delete file '{f}'. ({type(ex)}: {ex})"
            logging.error(msg)
            QtWidgets.QMessageBox.critical(self, self.tr("Web Map Service"), self.tr(msg))
        logging.debug("cache has been cleaned (%i files removed).", removed_files)

    def squash_multiple_images(self, imgs):
        """
        Lay the images on top of each other from 0 to n and return the product
        """
        background = imgs[0]
        if len(imgs) > 1:
            for foreground in imgs[1:]:
                background.paste(foreground, (0, 0), foreground.convert("RGBA"))

        return background

    def append_multiple_images(self, imgs):
        """
        Stack the list of images vertically and return the product
        """
        images = [x for x in imgs if x]
        if images:
            # Add border around seperate legends
            if len(images) > 1:
                images = [ImageOps.expand(x, border=1, fill="black") for x in images]
            max_height = int((self.view.fig.get_size_inches() * self.view.fig.get_dpi())[1] * 0.99)
            width = max([image.width for image in images])
            height = sum([image.height for image in images])
            result = Image.new("RGBA", (width, height))
            current_height = 0
            for i, image in enumerate(images):
                result.paste(image, (0, current_height - i))
                current_height += image.height

            if max_height < result.height:
                result.thumbnail((result.width, max_height), Image.ANTIALIAS)
            return result

        ################################################################################

#
# CLASS VSecWMSControlWidget
#


class VSecWMSControlWidget(WMSControlWidget):
    """Subclass of WMSControlWidget that extends the WMS client to
       handle (non-standard) vertical sections.
    """

    def __init__(self, parent=None, default_WMS=None, waypoints_model=None,
                 view=None, wms_cache=None):
        super(VSecWMSControlWidget, self).__init__(
            parent=parent, default_WMS=default_WMS, wms_cache=wms_cache, view=view)
        self.waypoints_model = waypoints_model
        self.btGetMap.clicked.connect(self.get_all_maps)

    def get_all_maps(self):
        if self.multilayers.cbMultilayering.isChecked():
            self.get_vsec(self.multilayers.get_active_layers())
        else:
            self.get_vsec([self.multilayers.get_current_layer()])

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance from which the waypoints
           are obtained.
        """
        self.waypoints_model = model

    @QtCore.Slot()
    def call_get_vsec(self):
        if self.btGetMap.isEnabled() and self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
            self.get_all_maps()

    def get_vsec(self, layers=None):
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
        for waypoint in self.waypoints_model.all_waypoint_data():
            path_string += f"{waypoint.lat:.2f},{waypoint.lon:.2f},"
        path_string = path_string[:-1]

        # Determine the current size of the vertical section plot on the
        # screen in pixels. The image will be retrieved in this size.
        width, height = self.view.get_plot_size_in_px()

        # Retrieve the image.
        if not layers:
            layers = [self.multilayers.get_current_layer()]
        layers.sort(key=lambda x: self.multilayers.get_multilayer_priority(x))

        args = []
        for i, layer in enumerate(layers):
            transparent = self.cbTransparent.isChecked() if i == 0 else True
            args.extend(self.retrieve_image(layer, crs, bbox, path_string, width, height, transparent))

        self.fetch.emit(args)

    def display_retrieved_image(self, imgs, legend_imgs, layer, style, init_time, valid_time, level):
        # Plot the image on the view canvas.
        self.view.draw_image(self.squash_multiple_images(imgs))
        self.view.draw_legend(self.append_multiple_images(legend_imgs))
        style_title = self.multilayers.get_current_layer().get_style()
        self.view.draw_metadata(title=self.multilayers.get_current_layer().layerobj.title,
                                init_time=init_time,
                                valid_time=valid_time,
                                style=style_title)

    def is_layer_aligned(self, layer):
        crss = getattr(layer, "crsOptions", None)
        return crss is not None and any(crs.startswith("VERT") for crs in crss)

#
# CLASS HSecWMSControlWidget
#


class HSecWMSControlWidget(WMSControlWidget):
    """Subclass of WMSControlWidget that extends the WMS client to
       handle (standard) horizontal sections, i.e. maps.
    """

    def __init__(self, parent=None, default_WMS=None, view=None, wms_cache=None):
        super(HSecWMSControlWidget, self).__init__(
            parent=parent, default_WMS=default_WMS, wms_cache=wms_cache, view=view)
        self.btGetMap.clicked.connect(self.get_all_maps)

    def level_changed(self):
        super().level_changed()
        self.view.waypoints_interactor.update()

    def get_map(self, layers=None):
        """Slot that retrieves the map and passes the image
           to the view.
        """
        # Get coordinate reference system and bounding box from the map
        # object in the view.
        crs = self.view.get_crs()
        bbox = self.view.getBBOX()

        # Determine the current size of the vertical section plot on the
        # screen in pixels. The image will be retrieved in this size.
        width, height = self.view.get_plot_size_in_px()

        if not layers:
            layers = [self.multilayers.get_current_layer()]

        layers.sort(key=lambda x: self.multilayers.get_multilayer_priority(x))

        args = []
        for i, layer in enumerate(layers):
            transparent = self.cbTransparent.isChecked() if i == 0 else True
            bbox_tmp = tuple(bbox)
            wms = self.multilayers.layers[layer.wms_name]["wms"]
            if wms.version == "1.3.0" and crs.startswith("EPSG") and int(crs[5:]) in axisorder_yx:
                bbox_tmp = (bbox[1], bbox[0], bbox[3], bbox[2])
            args.extend(self.retrieve_image(layer, crs, bbox_tmp, None, width, height, transparent))

        self.fetch.emit(args)

    def display_retrieved_image(self, imgs, legend_imgs, layer, style, init_time, valid_time, level):
        # Plot the image on the view canvas.
        style_title = self.multilayers.get_current_layer().get_style()
        self.view.draw_metadata(title=self.multilayers.get_current_layer().layerobj.title,
                                init_time=init_time,
                                valid_time=valid_time,
                                level=level,
                                style=style_title)
        self.view.draw_image(self.squash_multiple_images(imgs))
        self.view.draw_legend(self.append_multiple_images(legend_imgs))
        self.view.waypoints_interactor.update()

    def is_layer_aligned(self, layer):
        crss = getattr(layer, "crsOptions", None)
        return crss is not None and not any(crs.startswith("VERT") for crs in crss) \
            and not any(crs.startswith("LINE") for crs in crss)


class LSecWMSControlWidget(WMSControlWidget):
    """Subclass of WMSControlWidget that extends the WMS client to
       handle (non-standard) linear sections.
    """

    def __init__(self, parent=None, default_WMS=None, waypoints_model=None,
                 view=None, wms_cache=None):
        super(LSecWMSControlWidget, self).__init__(
            parent=parent, default_WMS=default_WMS, wms_cache=wms_cache, view=view)
        self.waypoints_model = waypoints_model
        self.btGetMap.clicked.connect(self.get_all_maps)

    def get_all_maps(self):
        if self.multilayers.cbMultilayering.isChecked():
            self.get_lsec(self.multilayers.get_active_layers())
        else:
            self.get_lsec([self.multilayers.get_current_layer()])

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance from which the waypoints
           are obtained.
        """
        self.waypoints_model = model

    @QtCore.Slot()
    def call_get_lsec(self):
        if self.btGetMap.isEnabled() and self.cbAutoUpdate.isChecked() and not self.layerChangeInProgress:
            self.get_all_maps()

    def get_lsec(self, layers=None):
        """Slot that retrieves the linear plot and passes the image
                   to the view.
                """
        # Specify the coordinate reference system for the request. We will
        # use the non-standard "LINE:1" to query the MSS WMS Server for
        # a linear plot.
        crs = "LINE:1"
        bbox = self.view.getBBOX()

        # Get lat/lon/alt coordinates of flight track and convert to string for URL.
        path_string = ""
        for waypoint in self.waypoints_model.all_waypoint_data():
            path_string += f"{waypoint.lat:.2f},{waypoint.lon:.2f},{waypoint.pressure},"
        path_string = path_string[:-1]

        # Retrieve the image.
        if not layers:
            layers = [self.multilayers.get_current_layer()]
        layers.sort(key=lambda x: self.multilayers.get_multilayer_priority(x))

        args = []
        for i, layer in enumerate(layers):
            args.extend(self.retrieve_image(layer, crs, bbox, path_string, transparent=False, format="text/xml"))

        self.fetch.emit(args)

    def display_retrieved_image(self, imgs, legend_imgs, layer, style, init_time, valid_time, level):
        # Plot the image on the view canvas.
        layers = self.multilayers.get_active_layers() if self.multilayers.cbMultilayering.isChecked() else \
            [self.multilayers.get_current_layer()]
        layers.sort(key=lambda x: self.multilayers.get_multilayer_priority(x))
        colors = [layer.color for layer in layers]
        scales = [layer.get_style() for layer in layers]
        self.view.draw_image(imgs, colors, scales)
        self.view.draw_legend(self.append_multiple_images(legend_imgs))
        style_title = self.multilayers.get_current_layer().get_style()
        self.view.draw_metadata(title=self.multilayers.get_current_layer().layerobj.title,
                                init_time=init_time,
                                valid_time=valid_time,
                                style=style_title)

    def is_layer_aligned(self, layer):
        crss = getattr(layer, "crsOptions", None)
        return crss is not None and any(crs.startswith("LINE") for crs in crss)
