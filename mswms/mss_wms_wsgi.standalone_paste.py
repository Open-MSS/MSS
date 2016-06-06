#!/usr/bin/env python
"""WSGI module for MSS WMS server that provides access to ECMWF forecast data.

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

The module implements a Web Map Service 1.1.1 interface to provide forecast data
from numerical weather predictions to the Mission Support User Interface.
Supported operations are GetCapabilities and GetMap for (WMS 1.1.1 compliant)
maps and (non-compliant) vertical sections.

For more information on WMS, see
       http://www.opengeospatial.org/standards/wms

The module can be run with the Python PASTE framework as a stand-alone
server (simply execute this file with Python), or be integrated into an
existing Apache installation (for usage in an production environment).

For an introduction on WSGI and Paste, see
       http://pythonpaste.org/do-it-yourself-framework.html

A good starting point to understand the program is to look at the main
program at the end of the file.

USAGE:
======

1) Configure the WMS server by modifying the settings in mss_wms_settings.py
(address, products that shall be offered, ..).

2) Start a server by simply executing this file. Shutdown the server
with Ctrl+C. If you need to keep the server running on a remote
computer, use the Unix 'nohup' command and provide a logfile to which
all output can be written.

The following command line arguments are supported:

a) "--ssh" Starts the server in ssh-tunnel mode, i.e. the GetMap URL
specified in the capabilities document points to localhost instead of
to the machine name specified in mss_wms_settings.py. This is only
required when you run the WMS on a remote machine and want to access
it through an ssh tunnel (see the "-L" option of ssh). If you use an
ssh tunnel and get an error message in the MSUI that the WMS server
cannot be found, you likely forgot this option.

b) "<filename>" If you specify a filename on the command line, all
output will be written to this file instead of to standard out.

Example:
                ./mss_wms_wsgi.py --ssh wms.log
will start the server in ssh-tunnel mode and write all output to the file
"wms.log".

3) If you want to define new visualisation styles, the files to put them
are mpl_hsec_styles.py and mpl_vsec_styles for maps and vertical sections,
respectively.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import logging
import xml.dom.minidom
from datetime import datetime
import socket

# related third party imports
import paste.request
import paste.util.multidict
from paste.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPServiceUnavailable

# local application imports
from mslib import mss_config
import mss_plot_driver
import mss_wms_settings

"""
CaseInsensitiveMulitDict
"""


# The following class is used to make the module case-insensitive for
# the URL query parameters (i.e. it doesn't matter whether the client
# requests GetMap or getMAP).
class CaseInsensitiveMultiDict(paste.util.multidict.MultiDict):
    """Extension to paste.util.multidict.MultiDict that makes the MultiDict
       case-insensitive.

    The only overridden method is __getitem__(), which converts string keys
    to lower case before carrying out comparisons.

    See ../paste/util/multidict.py as well as
      http://stackoverflow.com/questions/2082152/case-insensitive-dictionary
    """

    def __getitem__(self, key):
        if hasattr(key, 'lower'):
            key = key.lower()
        for k, v in self._items:
            if hasattr(k, 'lower'):
                k = k.lower()
            if k == key:
                return v
        raise KeyError(repr(key))


"""
CLASS MSS_WMSResponse
"""


class MSS_WMSResponse(object):
    """WSGI handler for WMS server. The Web Map Service corresponds to version
       1.1.1 of the OGC WMS specification.
    """

    # The following template is used to generate the capabilities document.
    capabilitiesxmltemplate = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <!DOCTYPE WMT_MS_Capabilities SYSTEM "http://www.digitalearth.gov/wmt/xml/capabilities_1_1_1.dtd">
    <WMT_MS_Capabilities version="1.1.1" updateSequence="0">
      <Service>
        <Name>OGC:WMS</Name>
        <Title>Mission Support System Web Map Service</Title>
        <Abstract>Access to forecast products.</Abstract>
        <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://www.your-server.de/"/>
        <ContactInformation>
          <ContactPersonPrimary>
            <ContactPerson>Your Name</ContactPerson>
            <ContactOrganization>Your Institute</ContactOrganization>
          </ContactPersonPrimary>
          <ContactAddress>
            <AddressType>postal</AddressType>
            <Address>Street</Address>
            <City>City</City>
            <StateOrProvince></StateOrProvince>
            <PostCode>12345</PostCode>
            <Country>Germany</Country>
          </ContactAddress>
        </ContactInformation>
        <Fees>none</Fees>
        <AccessConstraints>This service is intended for research purposes only.</AccessConstraints>
      </Service>
      <Capability>
        <Request>
          <GetCapabilities>
            <Format>application/vnd.ogc.wms_xml</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                  xlink:href="http://localhost:8081/mss_wms?"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetCapabilities>
          <GetMap>
            <Format>image/png</Format>
            <DCPType>
              <HTTP>
                <Get>
                  <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                  xlink:href="http://localhost:8081/mss_wms?"/>
                </Get>
              </HTTP>
            </DCPType>
          </GetMap>
        </Request>
        <Exception>
          <Format>application/vnd.ogc.se_xml</Format>
        </Exception>
        <Layer>
          <Title>Mission Support WMS Server</Title>
          <Abstract>Mission Support WMS Server</Abstract>
        </Layer>
      </Capability>
    </WMT_MS_Capabilities>
    """

    # Template for creating service exception XMLs.
    exceptionxmltemplate = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <!DOCTYPE ServiceExceptionReport SYSTEM "http://www.digitalearth.gov/wmt/xml/exception_1_1_1.dtd">
    <ServiceExceptionReport version="1.1.1">
    </ServiceExceptionReport>
    """

    def __init__(self, data_access_dict, address="localhost:8081"):
        """The constructor initialises the plot drivers.
        """
        logging.debug("*****************************************************")
        logging.debug("DLR/IPA Mission Support System")
        logging.debug("Web Map Service (WMS), WSGI module.")
        logging.debug("*****************************************************")
        logging.debug("Initialising a new WMS server with data root paths:")
        for key in data_access_dict.keys():
            root_path = data_access_dict[key].get_datapath()
            logging.debug("- %s: %s", key, root_path)

        # WSGI return headers.
        self.headers = []

        # Style registry and driver for horizontal sections.
        self.hsec_layer_registry = {}
        self.hsec_drivers = {}
        for key in data_access_dict.keys():
            self.hsec_drivers[key] = mss_plot_driver.HorizontalSectionDriver(
                data_access_dict[key])

        # Style registry and driver for vertical sections.
        self.vsec_layer_registry = {}
        self.vsec_drivers = {}
        for key in data_access_dict.keys():
            self.vsec_drivers[key] = mss_plot_driver.VerticalSectionDriver(
                data_access_dict[key])

        # Insert correct http address into capabilities template.
        self.capabilitiesxmltemplate = self.capabilitiesxmltemplate.replace(
            "localhost:8081", address)

        # Variable to lock simultaneous requests (see __call__ for more
        # information).
        self.processing_request = False

    def __call__(self, environ, start_response):
        """Main routine that handles server requests. Parses the URL to
           determine the requested action (GetCapabilities, GetMap, GetVSec
           etc.) and calls the corresponding method.

        Uses a CaseInsensitiveMultiDict to make the parameters in the URL query
        string case insensitive.
        """
        # Simple safety check to make sure one class instance of this WSGI
        # application is not executed twice or more times simoultaneously.
        # While Matplotlib's OO-interface should work with simultaneous
        # requests, a single class instance does not: If a web server
        # with multiple threads is required, multiple instances of this
        # WSGI app should be created.
        if self.processing_request:
            return HTTPServiceUnavailable(detail="This service is currently "
                                                 "active and does not support "
                                                 "simultaneous requests. Please try "
                                                 "again in a few seconds.")(environ, start_response)

        # Block sinultaneous class instance calls by setting the
        # processing_request flag to True. The following code is embedded
        # in a try..except block so if an error occurs, we can reset
        # the flag (otherwise the application would be locked forever).
        self.processing_request = True
        try:

            # WSGI return headers.
            self.headers = []

            # Get the base URL and parse the query parameters.
            path_info = environ.get('PATH_INFO', '')
            query = CaseInsensitiveMultiDict(paste.request.parse_dict_querystring(environ))
            logging.debug("REQUEST: %s, %s", path_info, query)

            # Deny accesses to other URLs than /mss_wms
            if path_info != "/mss_wms":
                logging.debug("\tAccess denied.")
                self.processing_request = False
                return HTTPNotFound()(environ, start_response)

            # Handle GetCapabilities, GetMap etc. requests.
            type_ = str(query.get('REQUEST', None))
            if type_.lower() == 'getcapabilities':
                return_data = self.get_capabilities(environ)
                if not self.is_service_exception(return_data):
                    self.headers.append(('Content-type', 'text/xml'))
                else:
                    # self.headers.append(('Content-type', 'application/vnd.ogc.se_xml'))
                    self.headers.append(('Content-type', 'text/xml'))
            elif type_.lower() in ['getmap', 'getvsec']:
                return_data, return_format = self.produce_plot(environ, type_)
                if not self.is_service_exception(return_data):
                    # self.headers.append(('Content-type', 'image/png'))
                    self.headers.append(('Content-type', return_format.lower()))
                else:
                    # self.headers.append(('Content-type', 'application/vnd.ogc.se_xml'))
                    self.headers.append(('Content-type', 'text/xml'))
            else:
                return_data = self.service_exception(text='Invalid REQUEST "%s"' % type_)
                # self.headers.append(('Content-type', 'application/vnd.ogc.se_xml'))
                self.headers.append(('Content-type', 'text/xml'))

            # Start the HTTP response and return the result.
            start_response('200 OK', self.headers)
            self.processing_request = False
            return [return_data]

        # If anything in the execution of the WMS goes wrong (which, of course,
        # is not supposed to.. :) ), make sure the service doesn't block
        # because of the set processing_request flag.
        except:
            self.processing_request = False
            raise

    def register_hsec_layer(self, datasets, layer_class):
        """Register horizontal section layer in internal dict of layers.

        Arguments:
        datasets -- list of strings describing the datasets with which the
                    layer shall be registered.
        layer_class -- class of which the layer instances shall be created.
        """
        # Loop over all provided dataset names. Create an instance of the
        # provided layer class for all datasets and register the layer
        # instances with the datasets.
        for dataset in datasets:
            layer = layer_class()
            logging.debug("registering horizontal section layer %s with "
                          "dataset %s", layer.name, dataset)
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.hsec_layer_registry.keys():
                if dataset in self.hsec_drivers.keys():
                    self.hsec_layer_registry[dataset] = {}
                else:
                    raise ValueError("dataset %s not available" % dataset)
            layer.set_driver(self.hsec_drivers[dataset])
            self.hsec_layer_registry[dataset][layer.name] = layer

    def register_vsec_layer(self, datasets, layer_class):
        """Register vertical section layer in internal dict of layers.

        See register_hsec_layer() for further information.
        """
        # Loop over all provided dataset names. Create an instance of the
        # provided layer class for all datasets and register the layer
        # instances with the datasets.
        for dataset in datasets:
            layer = layer_class()
            logging.debug("registering vertical section layer %s with "
                          "dataset %s", layer.name, dataset)
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.vsec_layer_registry.keys():
                if dataset in self.vsec_drivers.keys():
                    self.vsec_layer_registry[dataset] = {}
                else:
                    raise ValueError("dataset %s not available" % dataset)
            layer.set_driver(self.vsec_drivers[dataset])
            self.vsec_layer_registry[dataset][layer.name] = layer

    def service_exception(self, code=None, text=""):
        """Create a service exception XML from the XML template defined above.

        Arguments:
        code -- WMS 1.1.1 exception code, see p.51 of the WMS 1.1.1 standard.
                This parameter is optional.
        text -- arbitrary error message

        Returns an XML as string.
        """
        logging.debug("creating service exception..")
        # Parse the XML template into a xml.dom.minidom.Document object.
        xmlstrings = self.exceptionxmltemplate.splitlines()
        xmlstrings = [line.strip() for line in xmlstrings]
        dom = xml.dom.minidom.parseString("".join(xmlstrings))

        # Get the root ServiceExceptionReport element, add ServiceException
        # element and the error message.
        rootelement = dom.getElementsByTagName("ServiceExceptionReport")[0]
        exceptionelement = dom.createElement("ServiceException")
        if code is not None:
            exceptionelement.setAttribute("code", code)
        exceptionelement.appendChild(dom.createTextNode(text))
        rootelement.appendChild(exceptionelement)

        return dom.toprettyxml(indent="  ")

    def is_service_exception(self, var):
        """Returns True if the given parameter is an XML that contains
           a service exception.
        """
        if isinstance(var, str) or isinstance(var, unicode):
            if var.find("<ServiceException") > 1:
                return True
        return False

    def get_capabilities(self, environ):
        """Create a capabilities document from the XML template defined above.
        """
        logging.debug("creating capabilities document..")
        # Parse the XML template into a xml.dom.minidom.Document object.
        capstrings = self.capabilitiesxmltemplate.splitlines()
        capstrings = [line.strip() for line in capstrings]
        dom = xml.dom.minidom.parseString("".join(capstrings))

        # Get the root capabilities element. If vertical sections are
        # registered, we need to create a new layer element within the
        # capabilities element that will become parent to all vertical
        # section layers.
        rootcapelem = dom.getElementsByTagName('Capability')[0]

        # 1) Write information about horizontal sections (maps).
        # ======================================================

        # Make use of layer property inheritance: Get a pointer to the
        # root layer element in the document. All registered hsec layers
        # will be advertised as sublayers in the document, thus inheriting
        # properties set for the root layer.
        rootlayerelem = dom.getElementsByTagName('Layer')[0]

        # Advertise registered map layers.
        for dataset in self.hsec_layer_registry.keys():
            for layer in self.hsec_layer_registry[dataset].values():

                layere = dom.createElement('Layer')

                # Name
                layername = dom.createElement('Name')
                layername.appendChild(dom.createTextNode("%s.%s" % (dataset, layer.name)))
                layere.appendChild(layername)

                # Title, abstract, queryable.
                if layer.title:
                    layertitle = dom.createElement('Title')
                    layertitle.appendChild(dom.createTextNode(layer.title))
                    layere.appendChild(layertitle)
                if layer.abstract:
                    layerabstract = dom.createElement('Abstract')
                    layerabstract.appendChild(dom.createTextNode(layer.abstract))
                    layere.appendChild(layerabstract)
                if layer.queryable:
                    layere.setAttribute('queryable', '0')

                    # SRS.
                for crs in layer.supported_crs():
                    layerepsg = dom.createElement('SRS')
                    layerepsg.appendChild(dom.createTextNode(crs))
                    layere.appendChild(layerepsg)

                # Bounding box.
                latlonbb = dom.createElement('LatLonBoundingBox')
                latlonbb.setAttribute('minx', '-180')
                latlonbb.setAttribute('miny', '-90')
                latlonbb.setAttribute('maxx', '180')
                latlonbb.setAttribute('maxy', '90')
                layere.appendChild(latlonbb)

                # Time dimensions, if required by the layer.
                if layer.uses_time_dimensions():
                    dim = dom.createElement("Dimension")
                    dim.setAttribute("name", "TIME")
                    dim.setAttribute("units", "ISO8601")  # cf http://de.wikipedia.org/wiki/ISO_8601
                    layere.appendChild(dim)

                    dim = dom.createElement("Dimension")
                    dim.setAttribute("name", "INIT_TIME")
                    dim.setAttribute("units", "ISO8601")  # cf http://de.wikipedia.org/wiki/ISO_8601
                    layere.appendChild(dim)

                # Elevation dimension, if required by the layer.
                el_str = layer.get_elevations()
                if len(el_str) > 0:
                    dim = dom.createElement("Dimension")
                    dim.setAttribute("name", "ELEVATION")
                    dim.setAttribute("units", layer.get_elevation_units())
                    layere.appendChild(dim)

                # Extents of time and elevation dimensions.
                if layer.uses_time_dimensions():
                    dimext = dom.createElement("Extent")
                    dimext.setAttribute("name", "TIME")
                    vt_str = [dt.strftime("%Y-%m-%dT%H:%M:%SZ") for dt
                              in layer.get_all_valid_times()]
                    vt_str = ",".join(vt_str)
                    dimext.appendChild(dom.createTextNode(vt_str))
                    layere.appendChild(dimext)

                    dimext = dom.createElement("Extent")
                    dimext.setAttribute("name", "INIT_TIME")
                    it_str = [dt.strftime("%Y-%m-%dT%H:%M:%SZ") for dt
                              in layer.get_init_times()]
                    it_str = ",".join(it_str)
                    dimext.appendChild(dom.createTextNode(it_str))
                    layere.appendChild(dimext)

                if len(el_str) > 0:
                    dimext = dom.createElement("Extent")
                    dimext.setAttribute("name", "ELEVATION")
                    dimext.setAttribute("default", el_str[-1])
                    el_str = ",".join(el_str)
                    dimext.appendChild(dom.createTextNode(el_str))
                    layere.appendChild(dimext)

                # layerbbox = ElementTree.Element('BoundingBox')
                # layerbbox.set('SRS', '')
                # layerbbox.set('minx', str(env.minx))
                # layerbbox.set('miny', str(env.miny))
                # layerbbox.set('maxx', str(env.maxx))
                # layerbbox.set('maxy', str(env.maxy))
                # layere.appendChild(layerbbox)

                # Layer styles, if available.
                if type(layer.styles) is list:
                    for style_name, style_title in layer.styles:
                        style = dom.createElement("Style")
                        stylename = dom.createElement('Name')
                        stylename.appendChild(dom.createTextNode(style_name))
                        style.appendChild(stylename)
                        styletitle = dom.createElement('Title')
                        styletitle.appendChild(dom.createTextNode(style_title))
                        style.appendChild(styletitle)
                        layere.appendChild(style)

                rootlayerelem.appendChild(layere)

        # 2) Write information about non-standard vertical section layers.
        # ================================================================

        if len(self.vsec_layer_registry) > 0:
            # If any vertical sections are registered, create a new parent
            # layer for them.
            rootlayerelem = dom.createElement('Layer')
            rootcapelem.appendChild(rootlayerelem)

            layertitle = dom.createElement('Title')
            layertitle.appendChild(dom.createTextNode("Vertical Sections of ECMWF Forecasts."))
            rootlayerelem.appendChild(layertitle)

            # Advertise registered vertical sections.
            for dataset in self.vsec_layer_registry.keys():
                for layer in self.vsec_layer_registry[dataset].values():
                    layere = dom.createElement('Layer')

                    # Name.
                    layername = dom.createElement('Name')
                    layername.appendChild(dom.createTextNode("%s.%s" % (dataset, layer.name)))
                    layere.appendChild(layername)

                    # Title, abstract, queryable.
                    if layer.title:
                        layertitle = dom.createElement('Title')
                        layertitle.appendChild(dom.createTextNode(layer.title))
                        layere.appendChild(layertitle)
                    if layer.abstract:
                        layerabstract = dom.createElement('Abstract')
                        layerabstract.appendChild(dom.createTextNode(layer.abstract))
                        layere.appendChild(layerabstract)
                    if layer.queryable:
                        layere.setAttribute('queryable', '1')

                    # SRS.
                    for crs in layer.supported_crs():
                        layerepsg = dom.createElement('SRS')
                        layerepsg.appendChild(dom.createTextNode(crs))
                        layere.appendChild(layerepsg)

                    # Bounding box.
                    # TODO: This should become the area in which a vsec is allowed.
                    latlonbb = dom.createElement('LatLonBoundingBox')
                    latlonbb.setAttribute('minx', '-180')
                    latlonbb.setAttribute('miny', '-90')
                    latlonbb.setAttribute('maxx', '180')
                    latlonbb.setAttribute('maxy', '90')
                    layere.appendChild(latlonbb)

                    # Time dimensions, if required by the layer.
                    if layer.uses_time_dimensions():
                        dim = dom.createElement("Dimension")
                        dim.setAttribute("name", "TIME")
                        dim.setAttribute("units", "ISO8601")  # cf http://de.wikipedia.org/wiki/ISO_8601
                        layere.appendChild(dim)

                        dim = dom.createElement("Dimension")
                        dim.setAttribute("name", "INIT_TIME")
                        dim.setAttribute("units", "ISO8601")  # cf http://de.wikipedia.org/wiki/ISO_8601
                        layere.appendChild(dim)

                        dimext = dom.createElement("Extent")
                        dimext.setAttribute("name", "TIME")
                        vt_str = [dt.strftime("%Y-%m-%dT%H:%M:%SZ") for dt
                                  in layer.get_all_valid_times()]
                        vt_str = ",".join(vt_str)
                        dimext.appendChild(dom.createTextNode(vt_str))
                        layere.appendChild(dimext)

                        dimext = dom.createElement("Extent")
                        dimext.setAttribute("name", "INIT_TIME")
                        it_str = [dt.strftime("%Y-%m-%dT%H:%M:%SZ") for dt
                                  in layer.get_init_times()]
                        it_str = ",".join(it_str)
                        dimext.appendChild(dom.createTextNode(it_str))
                        layere.appendChild(dimext)

                    # Layer styles, if available.
                    if type(layer.styles) is list:
                        for style_name, style_title in layer.styles:
                            style = dom.createElement("Style")
                            stylename = dom.createElement('Name')
                            stylename.appendChild(dom.createTextNode(style_name))
                            style.appendChild(stylename)
                            styletitle = dom.createElement('Title')
                            styletitle.appendChild(dom.createTextNode(style_title))
                            style.appendChild(styletitle)
                            layere.appendChild(style)

                    rootlayerelem.appendChild(layere)

        logging.debug("returning capabilities document.")
        return dom.toprettyxml(indent="  ")

    def produce_plot(self, environ, mode):
        """Handler for a GetMap and GetVSec requests. Produces a plot with
           the parameters specified in the URL.

#TODO: Handle multiple layers. (mr, 2010-06-09)
#TODO: Cache the produced images: Check whether an image with the given
#      parameters has already been produced. (mr, 2010-08-18)
        """
        logging.debug("GetMap/GetVSec request. Interpreting parameters..")

        # 1) Get the query parameters from the URL.
        # =========================================
        query = CaseInsensitiveMultiDict(paste.request.parse_dict_querystring(environ))

        # 2) Evaluate query parameters:
        # =============================

        # Image size.
        figsize = float(query.get('WIDTH', 900)), float(query.get('HEIGHT', 600))
        logging.debug("  requested image size = %ix%i" % (figsize[0], figsize[1]))

        # Requested layers.
        layers = [layer for layer in query.get('LAYERS', '').strip().split(',') if layer]
        layer = layers[0] if len(layers) > 0 else ''
        if layer.find(".") > 0:
            dataset, layer = layer.split(".")
        else:
            dataset = None
        logging.debug("  requested dataset = %s, layer = %s" % (dataset, layer))

        # Requested style(s).
        styles = [style for style in query.get('STYLES', 'default').strip().split(',') if style]
        style = styles[0] if len(styles) > 0 else None
        logging.debug("  requested style = %s" % style)

        # Forecast initialisation time.
        init_time = query.get('DIM_INIT_TIME', None)
        if init_time is not None:
            try:
                init_time = datetime.strptime(init_time, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return self.service_exception(code="InvalidDimensionValue",
                                              text="DIM_INIT_TIME has wrong format "
                                                   "(needs to be 2005-08-29T13:00:00Z)"), None
        logging.debug("  requested initialisation time = %s" % init_time)

        # Forecast valid time.
        valid_time = query.get('TIME', None)
        if valid_time is not None:
            try:
                valid_time = datetime.strptime(valid_time, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return self.service_exception(code="InvalidDimensionValue",
                                              text="TIME has wrong format "
                                                   "(needs to be 2005-08-29T13:00:00Z)"), None
        logging.debug("  requested (valid) time = %s" % valid_time)

        # Coordinate reference system.
        crs = query.get('SRS', 'EPSG:4326')
        # Allow to request vertical sections via GetMap, if the specified CRS is
        # of type "VERT:??".
        msg = None
        if crs.startswith('VERT:LOGP'):
            mode = "GetVSec"
        elif crs.startswith('EPSG:'):
            try:
                epsg = int(crs[5:])
            except ValueError:
                msg = "The requested CRS %s is not supported." % crs
        else:
            msg = "The requested CRS %s is not supported." % crs

        if msg is not None:
            logging.error(msg)
            return self.service_exception(code="InvalidSRS", text=msg), None
        else:
            logging.debug("  requested coordinate reference system = %s" % crs)

        # Create a frameless figure (WMS) or one with title and legend
        # (MSS specific)? Default is WMS mode (frameless).
        noframe = query.get('FRAME', 'OFF').upper() == 'OFF'

        # Transparancy.
        transparent = query.get('TRANSPARENT', 'FALSE').upper() == 'TRUE'
        if transparent:
            logging.debug("  requested transparent image")

        # Return format (image/png, text/xml, etc.).
        return_format = query.get('FORMAT', 'IMAGE/PNG').lower()
        logging.debug("  requested return format = %s" % return_format)
        if return_format not in ["image/png", "text/xml"]:
            msg = "unsupported FORMAT: %s" % return_format
            logging.error(msg)
            return self.service_exception(code="InvalidFORMAT", text=msg), None

        # 3) Check GetMap/GetVSec-specific parameters and produce
        #    the image with the corresponding section driver.
        # =======================================================

        if mode == "GetMap":

            # Check requested layer.
            if (dataset not in self.hsec_layer_registry.keys()) or \
                    (layer not in self.hsec_layer_registry[dataset].keys()):
                msg = "Invalid LAYER '%s.%s' requested" % (dataset, layer)
                logging.error(msg)
                return self.service_exception(code="LayerNotDefined", text=msg), None

            # Check if the layer requires time information and if they are given.
            if self.hsec_layer_registry[dataset][layer].uses_time_dimensions():
                if init_time is None:
                    msg = "INIT_TIME not specified (use the " \
                          "DIM_INIT_TIME keyword)"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg), None
                if valid_time is None:
                    msg = "TIME not specified"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg), None

            # Check if the requested coordinate system is supported.
            if epsg not in self.hsec_layer_registry[dataset][layer].supported_epsg_codes():
                msg = "The requested CRS EPSG:%i is not supported." % epsg
                logging.error(msg)
                return self.service_exception(code="InvalidSRS", text=msg), None

            # Bounding box.
            try:
                bbox = [float(v) for v in query.get('BBOX',
                                                    '-180,-90,180,90').split(',')]
            except ValueError:
                msg = "Invalid BBOX: %s" % query.get("BBOX")
                logging.error(msg)
                return self.service_exception(text=msg), None

            # Vertical level, if applicable.
            level = query.get('ELEVATION', None)
            level = int(level) if level else None
            layer_datatypes = self.hsec_layer_registry[dataset][layer].required_datatypes()
            if (("ml" in layer_datatypes) or ("pl" in layer_datatypes)) \
                    and not level:
                # Use the default value.
                level = -1
                # return HTTPBadRequest("ELEVATION not specified (required for "\
                #                      "layer %s)." % layer)
            elif ("sfc" in layer_datatypes) and ("ml" not in layer_datatypes) \
                    and ("pl" not in layer_datatypes) and level:
                msg = "ELEVATION argument not applicable for layer " \
                      "%s. Please omit this argument." % layer
                logging.error(msg)
                return self.service_exception(text=msg), None

            plot_driver = self.hsec_drivers[dataset]
            try:
                plot_driver.set_plot_parameters(self.hsec_layer_registry[dataset][layer],
                                                bbox=bbox,
                                                level=level,
                                                init_time=init_time,
                                                valid_time=valid_time,
                                                style=style,
                                                figsize=figsize,
                                                epsg=epsg,
                                                noframe=noframe,
                                                transparent=transparent,
                                                return_format=return_format)
            except (IOError, ValueError) as e:
                logging.error("ERROR: %s" % e)
                msg = "The data corresponding to your request " \
                      "is not available. Please check the " \
                      "times and/or levels you have specified." \
                      "\n\nError message: %s" % e
                return self.service_exception(text=msg), None

        elif mode == "GetVSec":

            # Vertical secton path.
            path = query.get("PATH", None)
            if not path:
                return self.service_exception(text="PATH not specified"), None
            try:
                path = [float(v) for v in path.split(',')]
                path = [[lat, lon] for lat, lon in zip(path[0::2], path[1::2])]
            except ValueError:
                msg = "Invalid PATH: %s" % path
                logging.error(msg)
                return self.service_exception(text=msg), None
            logging.debug("VSEC PATH: %s", path)

            # Check requested layers.
            if (dataset not in self.vsec_layer_registry.keys()) or \
                    (layer not in self.vsec_layer_registry[dataset].keys()):
                msg = "Invalid LAYER '%s.%s' requested" % (dataset, layer)
                return self.service_exception(code="LayerNotDefined", text=msg), None

            # Check if the layer requires time information and if they are given.
            if self.vsec_layer_registry[dataset][layer].uses_time_dimensions():
                if init_time is None:
                    msg = "INIT_TIME not specified (use the " \
                          "DIM_INIT_TIME keyword)"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg), None
                if valid_time is None:
                    msg = "TIME not specified"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg), None

            # Bounding box (num interp. points, p_bot, num labels, p_top).
            try:
                bbox = [float(v) for v in query.get("BBOX", "101,1050,10,180").split(",")]
            except ValueError:
                msg = "Invalid BBOX: %s" % query.get("BBOX")
                logging.error(msg)
                return self.service_exception(text=msg), None

            plot_driver = self.vsec_drivers[dataset]
            try:
                plot_driver.set_plot_parameters(plot_object=self.vsec_layer_registry[dataset][layer],
                                                vsec_path=path,
                                                vsec_numpoints=bbox[0],
                                                vsec_path_connection="greatcircle",
                                                vsec_numlabels=bbox[2],
                                                init_time=init_time,
                                                valid_time=valid_time,
                                                style=style,
                                                bbox=bbox,
                                                figsize=figsize,
                                                noframe=noframe,
                                                transparent=transparent,
                                                return_format=return_format)
            except (IOError, ValueError) as e:
                logging.error("ERROR: %s" % e)
                msg = "The data corresponding to your request " \
                      "is not available. Please check the " \
                      "times and/or path you have specified." \
                      "\n\nError message: %s" % e
                return self.service_exception(text=msg), None

        # Produce the image.
        image = plot_driver.plot()

        # 4) Return the produced image.
        # =============================
        return image, return_format


"""
MAIN: integrated HTTP server
"""

if __name__ == '__main__':

    import sys

    # Parse command line arguments:
    # 1) --ssh enables the ssh-tunnel mode (GetMap request URL points to
    #          localhost)
    # 2) filename of a logfile, if the output should not be written to
    #    stdout.
    i = 1
    ssh_tunnel = False
    if len(sys.argv) > 1:
        ssh_tunnel = (sys.argv[1] == "--ssh")
        i = 2
    logfile = sys.argv[i] if len(sys.argv) > i else None

    if logfile is not None:
        # Log everything to "logfile".
        # TODO: Change this to write to a rotating log handler (so that the file size
        #      is kept constant). (mr, 2011-02-25)
        logging.basicConfig(filename=logfile,
                            level=logging.DEBUG,
                            format="%(asctime)s %(funcName)19s || %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    else:
        # Log everything, and send it to stderr.
        # See http://docs.python.org/library/logging.html for more information
        # on the Python logging module.
        logging.basicConfig(level=logging.DEBUG,
                            # format="%(levelname)s %(asctime)s %(funcName)19s || %(message)s",
                            format="%(asctime)s %(funcName)19s || %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # Check whether the server should bind to a particular IP address and port
    # (defined in mss_wms_settings). By default the server binds to localhost
    # on port 8081.
    host = "127.0.0.1"
    port = "8081"
    http_address = "localhost:%s" % port
    hostname = socket.gethostname()
    if hostname in mss_wms_settings.paste_ip_bind.keys():
        host = mss_wms_settings.paste_ip_bind[hostname]["host"]
        port = mss_wms_settings.paste_ip_bind[hostname]["port"]
        alias = mss_wms_settings.paste_ip_bind[hostname]["alias"]
        if not ssh_tunnel:
            http_address = "%s:%s" % (alias, port)
        else:
            http_address = "%s:%s" % ("localhost", port)

    # Initialise the WSGI application.
    app = MSS_WMSResponse(mss_config.nwpaccess, address=http_address)

    # Register horizontal section layers.
    for layer, datasets in mss_wms_settings.register_horizontal_layers:
        app.register_hsec_layer(datasets, layer)

    # Register vertical section styles.
    for layer, datasets in mss_wms_settings.register_vertical_layers:
        app.register_vsec_layer(datasets, layer)

    # Start the server.
    from paste import httpserver

    # Check if HTTP authentication should be enabled. See
    # http://pythonpaste.org/modules/auth.basic.html#module-paste.auth.basic
    # for more information.
    # NOTE: The OWSLIB WMS client that is used in MSUI only supports
    # basic HTTP authentication. To make the authentication process more
    # secure, e.g. by using Digest HTTP/1.1 Authentication, you have
    # to modify the client as well. See
    # http://pythonpaste.org/modules/auth.digest.html#module-paste.auth.digest
    # for more information. (mr, 2011-02-25).
    if mss_wms_settings.enable_basic_http_authentication:
        logging.debug("Enabling basic HTTP authentication. Username and "
                      "password required to access the service.")

        from paste.auth.basic import AuthBasicHandler
        import hashlib

        realm = 'DLR/IPA Mission Support Web Map Service'

        def authfunc(environ, username, password):
            for u, p in mss_wms_settings.allowed_users:
                if (u == username) and (p == hashlib.md5(password).hexdigest()):
                    return True
            return False

        app = AuthBasicHandler(app, realm, authfunc)

    # Set use_threadpool=True when using this software. The "False" setting is
    # used for development purposes to reduce debug output.
    use_threadpool = mss_wms_settings.paste_use_threadpool

    logging.debug("Starting PASTE httpserver on %s (%s), port %s. "
                  "Threads are %s." % (hostname, host, port,
                                       "enabled" if use_threadpool else "disabled"))
    logging.debug("SSH tunnel mode is %s. WMS access on client via %s"
                  % ("enabled" if ssh_tunnel else "disabled", http_address))

    httpserver.serve(app, host=host, port=port, use_threadpool=use_threadpool)
