"""WSGI module for MSS WMS server that provides access to ECMWF forecast data.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
             2016-2017 see AUTHORS

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


For an introduction on WSGI and Paste, see
       http://pythonpaste.org/do-it-yourself-framework.html

A good starting point to understand the program is to look at the main
program at the end of the file.

USAGE:
======

1) Configure the WMS server by modifying the settings in mss_wms_settings.py
(address, products that shall be offered, ..).

2) If you want to define new visualisation styles, the files to put them
are mpl_hsec_styles.py and mpl_vsec_styles for maps and vertical sections,
respectively.

AUTHORS:
========

* Marc Rautenhaus (mr)
* Omar Qunsul (oq)

"""
import os
import logging
from datetime import datetime
import traceback
import paste
import paste.request
import paste.util.multidict
import tempfile
import urlparse
from chameleon import PageTemplateLoader

try:
    import mss_wms_settings
except ImportError, e:
    logging.warning("Couldn't import mss_wms_settings (ImportError:'{}'), creating dummy config.".format(e))

    class mss_wms_settings(object):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        xml_template_location = os.path.join(base_dir, "xml_templates")
        service_name = "OGC:WMS"
        service_title = "Mission Support System Web Map Service"
        service_abstract = ""
        service_contact_person = ""
        service_contact_organisation = ""
        service_address_type = ""
        service_address = ""
        service_city = ""
        service_state_or_province = ""
        service_post_code = ""
        service_country = ""
        service_fees = ""
        service_access_constraints = "This service is intended for research purposes only."
        register_horizontal_layers = []
        register_vertical_layers = []
        enable_basic_http_authentication = False
        nwpaccess = {
            "ecmwf_NH_LL05": os.path.join(tempfile.gettempdir(), "mss/grid/ecmwf/netcdf")
        }
        __file__ = None

from mslib.mswms import mss_plot_driver

from mslib.mswms.case_insensitive_multi_dict import CaseInsensitiveMultiDict

# Logging the Standard Output, which will be added to the Apache Log Files
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(funcName)19s || %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Chameleon XMl template
base_dir = os.path.abspath(os.path.dirname(__file__))
xml_template_location = os.path.join(base_dir, "xml_templates")
templates = PageTemplateLoader(mss_wms_settings.__dict__.get("xml_template_location", xml_template_location))


class WMSServer(object):

    def __init__(self, data_access_dict):
        self.hsec_layer_registry = {}
        self.hsec_drivers = {}
        for key in data_access_dict.keys():
            self.hsec_drivers[key] = mss_plot_driver.HorizontalSectionDriver(
                data_access_dict[key])

        self.vsec_layer_registry = {}
        self.vsec_drivers = {}
        for key in data_access_dict.keys():
            self.vsec_drivers[key] = mss_plot_driver.VerticalSectionDriver(
                data_access_dict[key])

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
            logging.debug("registering horizontal section layer {} with "
                          "dataset {}".format(layer.name, dataset))
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.hsec_layer_registry.keys():
                if dataset in self.hsec_drivers.keys():
                    self.hsec_layer_registry[dataset] = {}
                else:
                    raise ValueError(u"dataset {} not available".format(dataset))
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
            logging.debug("registering vertical section layer {} with dataset {}".format(layer.name, dataset))
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.vsec_layer_registry.keys():
                if dataset in self.vsec_drivers.keys():
                    self.vsec_layer_registry[dataset] = {}
                else:
                    raise ValueError(u"dataset {} not available".format(dataset))
            layer.set_driver(self.vsec_drivers[dataset])
            self.vsec_layer_registry[dataset][layer.name] = layer

    def is_service_exception(self, var):
        """Returns True if the given parameter is an XML that contains
           a service exception.
        """
        if isinstance(var, (str, unicode)):
            if var.find("<ServiceException") > 1:
                return True
        return False

    def service_exception(self, code=None, text=""):
        """Create a service exception XML from the XML template defined above.

        Arguments:
        code -- WMS 1.1.1 exception code, see p.51 of the WMS 1.1.1 standard.
                This parameter is optional.
        text -- arbitrary error message

        Returns an XML as string.
        """
        logging.debug("creating service exception..")
        template = templates['service_exception.pt']
        # return_format = "text/xml"
        return [template(code=code, text=text), "text/xml"]

    def get_capabilities(self, server_url=None):
        template = templates['get_capabilities.pt']
        logging.debug("server-url {0}".format(server_url))

        # Horizontal Layers
        hsec_layers = []
        for dataset in self.hsec_layer_registry.keys():
            for layer in self.hsec_layer_registry[dataset].values():
                hsec_layers.append((dataset, layer))

        # Vertical Layers
        vsec_layers = []

        for dataset in self.vsec_layer_registry.keys():
            for layer in self.vsec_layer_registry[dataset].values():
                vsec_layers.append((dataset, layer))

        # return_format = 'text/xml'

        return_data = template(hsec_layers=hsec_layers, vsec_layers=vsec_layers, server_url=server_url,
                               service_name=mss_wms_settings.__dict__.get("service_name", "OGC:WMS"),
                               service_title=mss_wms_settings.__dict__.get("service_title",
                                                                           "Mission Support System Web Map Service"),
                               service_abstract=mss_wms_settings.__dict__.get("service_abstract", ""),
                               service_contact_person=mss_wms_settings.__dict__.get("service_contact_person", ""),
                               service_contact_organisation=mss_wms_settings.__dict__.get(
                                   "service_contact_organisation", ""),
                               service_address_type=mss_wms_settings.__dict__.get("service_address_type", ""),
                               service_address=mss_wms_settings.__dict__.get("service_address", ""),
                               service_city=mss_wms_settings.__dict__.get("service_city", ""),
                               service_state_or_province=mss_wms_settings.__dict__.get("service_state_or_province", ""),
                               service_post_code=mss_wms_settings.__dict__.get("service_post_code", ""),
                               service_country=mss_wms_settings.__dict__.get("service_country", ""),
                               service_fees=mss_wms_settings.__dict__.get("service_fees", ""),
                               service_access_constraints=mss_wms_settings.__dict__.get(
                                   "service_access_constraints",
                                   "This service is intended for research purposes only."))
        return return_data

    def produce_plot(self, environ, mode):
        """Handler for a GetMap and GetVSec requests. Produces a plot with
           the parameters specified in the URL.

        # TODO: Handle multiple layers. (mr, 2010-06-09)
        # TODO: Cache the produced images: Check whether an image with the given
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
        logging.debug("  requested image size = {:d}x{:d}".format(figsize[0], figsize[1]))

        # Requested layers.
        layers = [layer for layer in query.get('LAYERS', '').strip().split(',') if layer]
        layer = layers[0] if len(layers) > 0 else ''
        if layer.find(".") > 0:
            dataset, layer = layer.split(".")
        else:
            dataset = None
        logging.debug("  requested dataset = {}, layer = {}".format(dataset, layer))

        # Requested style(s).
        styles = [style for style in query.get('STYLES', 'default').strip().split(',') if style]
        style = styles[0] if len(styles) > 0 else None
        logging.debug(u"  requested style = {}".format(style))

        # Forecast initialisation time.
        init_time = query.get('DIM_INIT_TIME')
        if init_time is not None:
            try:
                init_time = datetime.strptime(init_time, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return self.service_exception(code="InvalidDimensionValue",
                                              text="DIM_INIT_TIME has wrong format "
                                              "(needs to be 2005-08-29T13:00:00Z)")
        logging.debug(u"  requested initialisation time = {}".format(init_time))

        # Forecast valid time.
        valid_time = query.get('TIME')
        if valid_time is not None:
            try:
                valid_time = datetime.strptime(valid_time, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return self.service_exception(code="InvalidDimensionValue",
                                              text="TIME has wrong format "
                                              "(needs to be 2005-08-29T13:00:00Z)")
        logging.debug(u"  requested (valid) time = {}".format(valid_time))

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
                msg = u"The requested CRS {} is not supported.".format(crs)
        else:
            msg = u"The requested CRS {} is not supported.".format(crs)

        if msg is not None:
            logging.error(msg)
            return self.service_exception(code="InvalidSRS", text=msg)
        else:
            logging.debug(u"  requested coordinate reference system = {}".format(crs))

        # Create a frameless figure (WMS) or one with title and legend
        # (MSS specific)? Default is WMS mode (frameless).
        noframe = query.get('FRAME', 'OFF').upper() == 'OFF'

        # Transparancy.
        transparent = query.get('TRANSPARENT', 'FALSE').upper() == 'TRUE'
        if transparent:
            logging.debug("  requested transparent image")

        # Return format (image/png, text/xml, etc.).
        return_format = query.get('FORMAT', 'IMAGE/PNG').lower()
        logging.debug(u"  requested return format = {}".format(return_format))
        if return_format not in ["image/png", "text/xml"]:
            msg = u"unsupported FORMAT: {}".format(return_format)
            logging.error(msg)
            return self.service_exception(code="InvalidFORMAT", text=msg)

        # 3) Check GetMap/GetVSec-specific parameters and produce
        #    the image with the corresponding section driver.
        # =======================================================

        if mode == "GetMap":

            # Check requested layer.
            if (dataset not in self.hsec_layer_registry.keys()) or \
               (layer not in self.hsec_layer_registry[dataset].keys()):
                msg = "Invalid LAYER '{}.{}' requested".format(dataset, layer)
                logging.error(msg)
                return self.service_exception(code="LayerNotDefined", text=msg)

            # Check if the layer requires time information and if they are given.
            if self.hsec_layer_registry[dataset][layer].uses_time_dimensions():
                if init_time is None:
                    msg = "INIT_TIME not specified (use the "\
                          "DIM_INIT_TIME keyword)"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg)
                if valid_time is None:
                    msg = "TIME not specified"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg)

            # Check if the requested coordinate system is supported.
            if epsg not in self.hsec_layer_registry[dataset][layer].supported_epsg_codes():
                msg = "The requested CRS EPSG:{:d} is not supported.".format(epsg)
                logging.error(msg)
                return self.service_exception(code="InvalidSRS", text=msg)

            # Bounding box.
            try:
                bbox = [float(v) for v in query.get('BBOX',
                                                    '-180,-90,180,90').split(',')]
            except ValueError:
                msg = u"Invalid BBOX: {}".format(query.get("BBOX"))
                logging.error(msg)
                return self.service_exception(text=msg)

            # Vertical level, if applicable.
            level = query.get('ELEVATION')
            level = int(level) if level else None
            layer_datatypes = self.hsec_layer_registry[dataset][layer].required_datatypes()
            if (("ml" in layer_datatypes) or ("pl" in layer_datatypes)) \
                    and not level:
                # Use the default value.
                level = -1
            elif ("sfc" in layer_datatypes) and ("ml" not in layer_datatypes) \
                    and ("pl" not in layer_datatypes) and level:
                msg = u"ELEVATION argument not applicable for layer " \
                      u"{}. Please omit this argument.".format(layer)
                logging.error(msg)
                return self.service_exception(text=msg)

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
                logging.error(u"ERROR: {}".format(e))
                msg = u"The data corresponding to your request " \
                      u"is not available. Please check the " \
                      u"times and/or levels you have specified." \
                      u"\n\nError message: {}".format(e)
                return self.service_exception(text=msg)

        elif mode == "GetVSec":

            # Vertical secton path.
            path = query.get("PATH")
            if not path:
                return self.service_exception(text="PATH not specified")
            try:
                path = [float(v) for v in path.split(',')]
                path = [[lat, lon] for lat, lon in zip(path[0::2], path[1::2])]
            except ValueError:
                msg = u"Invalid PATH: {}".format(path)
                logging.error(msg)
                return self.service_exception(text=msg)
            logging.debug("VSEC PATH: {}".format(path))

            # Check requested layers.
            if (dataset not in self.vsec_layer_registry.keys()) or \
                    (layer not in self.vsec_layer_registry[dataset].keys()):
                msg = "Invalid LAYER '{}.{}' requested".format(dataset, layer)
                return self.service_exception(code="LayerNotDefined", text=msg)

            # Check if the layer requires time information and if they are given.
            if self.vsec_layer_registry[dataset][layer].uses_time_dimensions():
                if init_time is None:
                    msg = "INIT_TIME not specified (use the "\
                          "DIM_INIT_TIME keyword)"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg)
                if valid_time is None:
                    msg = "TIME not specified"
                    logging.error(msg)
                    return self.service_exception(code="MissingDimensionValue", text=msg)

            # Bounding box (num interp. points, p_bot, num labels, p_top).
            try:
                bbox = [float(v) for v in query.get("BBOX", "101,1050,10,180").split(",")]
            except ValueError:
                msg = u"Invalid BBOX: {}".format(query.get("BBOX"))
                logging.error(msg)
                return self.service_exception(text=msg)

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
                logging.error(u"ERROR: {}".format(e))
                msg = u"The data corresponding to your request " \
                      u"is not available. Please check the " \
                      u"times and/or path you have specified." \
                      u"\n\nError message: {}".format(e)
                return self.service_exception(text=msg)

        # Produce the image.
        image = plot_driver.plot()

        # 4) Return the produced image.
        # =============================
        return image, return_format


app = WMSServer(mss_wms_settings.nwpaccess)

for layer, datasets in mss_wms_settings.register_horizontal_layers:
    app.register_hsec_layer(datasets, layer)

for layer, datasets in mss_wms_settings.register_vertical_layers:
    app.register_vsec_layer(datasets, layer)

# Simple Caching Solutions
# It maps the Requested URL to Tuble of ( data_format, response_body )
cache = {}


def application(environ, start_response):
    try:
        # Request info
        query = CaseInsensitiveMultiDict(paste.request.parse_dict_querystring(environ))
        logging.debug("ENVIRON: {}".format(environ))

        # Processing
        request = str(query.get('request'))
        return_data = ""
        return_format = 'text/plain'

        url = paste.request.construct_url(environ)
        server_url = urlparse.urljoin(url, urlparse.urlparse(url).path)

        if url in cache.keys():
            return_format, return_data = cache[url]
        else:
            if request.lower() == 'getcapabilities':
                return_format = 'text/xml'
                return_data = app.get_capabilities(server_url)
            elif request.lower() in ['getmap', 'getvsec']:
                return_data, return_format = app.produce_plot(environ, request)
                if not app.is_service_exception(return_data):
                    return_format = return_format.lower()  # MAYBE TO BE DELETED
                else:
                    return_format = "text/xml"

                # Saving the result in a cache
                cache[url] = (return_format, return_data)

        # Preparing the Response
        status = '200 OK'
        output = str(return_data)
        response_headers = [('Content-type', return_format), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)

        return [output]

    except Exception as e:
        status = '404 NOT FOUND'
        error_message = str(type(e)) + ": " + str(e)
        # ToDo add a config var to disable output, replace by standard text, "Internal Server error"
        error_message = error_message + "\n" + traceback.format_exc()
        logging.error(error_message)

        response_headers = [('Content-type', 'text/plain'),
                            ('Content-Length', str(len(error_message)))]
        start_response(status, response_headers)
        return [error_message]
