# -*- coding: utf-8 -*-
"""

    mslib.mswms.wms
    ~~~~~~~~~~~~~~~

    WSGI module for MSS WMS server that provides access to ECMWF forecast data.

    The module implements a Web Map Service 1.1.1/1.3.0 interface to provide forecast data
    from numerical weather predictions to the Mission Support User Interface.
    Supported operations are GetCapabilities and GetMap for (WMS 1.1.1/1.3.0 compliant)
    maps and (non-compliant) vertical sections.

    1) Configure the WMS server by modifying the settings in mss_wms_settings.py
    (address, products that shall be offered, ..).

    2) If you want to define new visualisation styles, the files to put them
    are mpl_hsec_styles.py and mpl_vsec_styles for maps and vertical sections,
    respectively.

    For more information on WMS, see http://www.opengeospatial.org/standards/wms

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr), Omar Qunsul (oq)
    :copyright: Copyright 2016-2017 Reimar Bauer
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

from future import standard_library

standard_library.install_aliases()

import os
import io
import logging
import traceback
import urllib.parse
from chameleon import PageTemplateLoader
from owslib.crs import axisorder_yx
from PIL import Image

from flask import request, make_response, render_template
from flask_httpauth import HTTPBasicAuth
from multidict import CIMultiDict
from mslib.utils import conditional_decorator
from mslib.utils import parse_iso_datetime
from mslib.index import app_loader

# Flask basic auth's documentation
# https://flask-basicauth.readthedocs.io/en/latest/#flask.ext.basicauth.BasicAuth.check_credentials

app = app_loader(__name__)
auth = HTTPBasicAuth()

realm = 'Mission Support Web Map Service'
app.config['realm'] = realm

try:
    import mss_wms_settings
except ImportError as ex:
    logging.warning("Couldn't import mss_wms_settings (ImportError:'%s'), creating dummy config.", ex)

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
        data = {}
        enable_basic_http_authentication = False
        __file__ = None

try:
    import mss_wms_auth
except ImportError as ex:
    logging.warning("Couldn't import mss_wms_auth (ImportError:'{%s), creating dummy config.", ex)

    class mss_wms_auth(object):
        allowed_users = [("mswms", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None

if mss_wms_settings.__dict__.get('enable_basic_http_authentication', False):
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    import hashlib

    def authfunc(username, password):
        for u, p in mss_wms_auth.allowed_users:
            if (u == username) and (p == hashlib.md5(password.encode('utf-8')).hexdigest()):
                return True
        return False

    @auth.verify_password
    def verify_pw(username, password):
        if request.authorization:
            auth = request.authorization
            username = auth.username
            password = auth.password
        return authfunc(username, password)

from mslib.mswms import mss_plot_driver
from mslib.utils import get_projection_params

# Logging the Standard Output, which will be added to the Apache Log Files
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(funcName)19s || %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Chameleon XMl template
base_dir = os.path.abspath(os.path.dirname(__file__))
xml_template_location = os.path.join(base_dir, "xml_templates")
templates = PageTemplateLoader(mss_wms_settings.__dict__.get("xml_template_location", xml_template_location))


def squash_multiple_images(imgs):
    with Image.open(io.BytesIO(imgs[0])) as background:
        background = background.convert("RGBA")
        if len(imgs) > 1:
            for img in imgs[1:]:
                with Image.open(io.BytesIO(img)) as foreground:
                    background.paste(foreground, (0, 0), foreground.convert("RGBA"))

        output = io.BytesIO()
        background.save(output, format="PNG")
        return output.getvalue()


class WMSServer(object):

    def __init__(self):
        """
        init method for wms server
        """
        data_access_dict = mss_wms_settings.data

        for key in data_access_dict:
            data_access_dict[key].setup()

        self.hsec_drivers = {}
        for key in data_access_dict:
            self.hsec_drivers[key] = mss_plot_driver.HorizontalSectionDriver(
                data_access_dict[key])

        self.vsec_drivers = {}
        for key in data_access_dict:
            self.vsec_drivers[key] = mss_plot_driver.VerticalSectionDriver(
                data_access_dict[key])

        self.hsec_layer_registry = {}
        for layer, datasets in mss_wms_settings.register_horizontal_layers:
            self.register_hsec_layer(datasets, layer)

        self.vsec_layer_registry = {}
        for layer, datasets in mss_wms_settings.register_vertical_layers:
            self.register_vsec_layer(datasets, layer)

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
            try:
                layer = layer_class(self.hsec_drivers[dataset])
            except KeyError as ex:
                logging.debug("ERROR: %s %s", type(ex), ex)
                continue
            logging.debug("registering horizontal section layer '%s' with dataset '%s'", layer.name, dataset)
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.hsec_layer_registry:
                if dataset in self.hsec_drivers:
                    self.hsec_layer_registry[dataset] = {}
                else:
                    raise ValueError("dataset '%s' not available", dataset)
            self.hsec_layer_registry[dataset][layer.name] = layer

    def register_vsec_layer(self, datasets, layer_class):
        """Register vertical section layer in internal dict of layers.

        See register_hsec_layer() for further information.
        """
        # Loop over all provided dataset names. Create an instance of the
        # provided layer class for all datasets and register the layer
        # instances with the datasets.
        for dataset in datasets:
            try:
                layer = layer_class(self.vsec_drivers[dataset])
            except KeyError as ex:
                logging.debug("ERROR: %s %s", type(ex), ex)
                continue
            logging.debug("registering vertical section layer '%s' with dataset '%s'", layer.name, dataset)
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.vsec_layer_registry:
                if dataset in self.vsec_drivers:
                    self.vsec_layer_registry[dataset] = {}
                else:
                    raise ValueError("dataset '%s' not available", dataset)
            self.vsec_layer_registry[dataset][layer.name] = layer

    def create_service_exception(self, code=None, text="", version="1.3.0"):
        """Create a service exception XML from the XML template defined above.

        Arguments:
        code -- WMS 1.1.1 exception code, see p.51 of the WMS 1.1.1 standard.
                This parameter is optional.
        text -- arbitrary error message

        Returns an XML as string.
        """
        if code is not None and code == "InvalidSRS" and version == "1.3.0":
            code = "InvalidCRS"
        logging.error("creating service exception code='%s' text='%s'.", code, text)
        template = templates['service_exception.pt' if version == "1.1.1" else "service_exception130.pt"]
        return template(code=code, text=text).encode("utf-8"), "text/xml"

    def get_capabilities(self, query, server_url=None):
        # ToDo find a more elegant method to do the same
        # Preferable we don't want a seperate data_access module to be configured
        data_access_dict = mss_wms_settings.data

        for key in data_access_dict:
            data_access_dict[key].setup()

        version = query.get("VERSION", "1.1.1")

        # Handle update sequence exceptions
        sequence = query.get("UPDATESEQUENCE")
        if sequence and int(sequence) == 0:
            return self.create_service_exception(
                code="CurrentUpdateSequence",
                text="Requested update sequence is the current",
                version=version)
        elif sequence and int(sequence) > 0:
            return self.create_service_exception(
                code="InvalidUpdateSequence",
                text="Requested update sequence is higher than current",
                version=version)

        template = templates['get_capabilities130.pt' if version == "1.3.0" else 'get_capabilities.pt']
        logging.debug("server-url '%s'", server_url)

        # Horizontal Layers
        hsec_layers = []
        for dataset in self.hsec_layer_registry:
            for layer in self.hsec_layer_registry[dataset].values():
                if layer.uses_inittime_dimension() and len(layer.get_init_times()) == 0:
                    logging.error("layer %s/%s has no init times!", layer, dataset)
                    continue
                if layer.uses_validtime_dimension() and len(layer.get_all_valid_times()) == 0:
                    logging.error("layer %s/%s has no valid times!", layer, dataset)
                    continue
                hsec_layers.append((dataset, layer))

        # Vertical Layers
        vsec_layers = []
        for dataset in self.vsec_layer_registry:
            for layer in self.vsec_layer_registry[dataset].values():
                if layer.uses_inittime_dimension() and len(layer.get_init_times()) == 0:
                    logging.error("layer %s/%s has no init times!", layer, dataset)
                    continue
                if layer.uses_validtime_dimension() and len(layer.get_all_valid_times()) == 0:
                    logging.error("layer %s/%s has no valid times!", layer, dataset)
                    continue
                vsec_layers.append((dataset, layer))

        settings = mss_wms_settings.__dict__
        return_data = template(hsec_layers=hsec_layers, vsec_layers=vsec_layers, server_url=server_url,
                               service_name=settings.get("service_name", "OGC:WMS"),
                               service_title=settings.get("service_title", "Mission Support System Web Map Service"),
                               service_abstract=settings.get("service_abstract", ""),
                               service_contact_person=settings.get("service_contact_person", ""),
                               service_contact_organisation=settings.get("service_contact_organisation", ""),
                               service_contact_position=settings.get("service_contact_position", ""),
                               service_email=settings.get("service_email", ""),
                               service_address_type=settings.get("service_address_type", ""),
                               service_address=settings.get("service_address", ""),
                               service_city=settings.get("service_city", ""),
                               service_state_or_province=settings.get("service_state_or_province", ""),
                               service_post_code=settings.get("service_post_code", ""),
                               service_country=settings.get("service_country", ""),
                               service_fees=settings.get("service_fees", ""),
                               service_access_constraints=settings.get(
                                   "service_access_constraints",
                                   "This service is intended for research purposes only."))
        return return_data.encode("utf-8"), "text/xml"

    def produce_plot(self, query, mode):
        """
        Handler for a GetMap and GetVSec requests. Produces a plot with
        the parameters specified in the URL.

        # TODO: Handle multiple layers. (mr, 2010-06-09)
        # TODO: Cache the produced images: Check whether an image with the given
        #      parameters has already been produced. (mr, 2010-08-18)
        """
        logging.debug("GetMap/GetVSec request. Interpreting parameters..")

        # Evaluate query parameters:
        # =============================

        version = query.get("VERSION", "1.1.1")

        # Image size.
        width = query.get('WIDTH', 900)
        height = query.get('HEIGHT', 600)
        figsize = float(width if width != "" else 900), float(height if height != "" else 600)
        logging.debug("  requested image size = %sx%s", figsize[0], figsize[1])

        # Requested layers.
        layers = [layer for layer in query.get('LAYERS', '').strip().split(',') if layer]
        images = []
        for index, layer in enumerate(layers):
            if layer.find(".") > 0:
                dataset, layer = layer.split(".")
            else:
                dataset = None
            logging.debug("  requested dataset = '%s', layer = '%s'", dataset, layer)

            # Requested style(s).
            styles = [style for style in query.get('STYLES', 'default').strip().split(',') if style]
            style = styles[0] if len(styles) > 0 else None
            logging.debug("  requested style = '%s'", style)

            # Forecast initialisation time.
            init_time = query.get('DIM_INIT_TIME')
            if init_time is not None:
                try:
                    init_time = parse_iso_datetime(init_time)
                except ValueError:
                    return self.create_service_exception(
                        code="InvalidDimensionValue",
                        text="DIM_INIT_TIME has wrong format (needs to be 2005-08-29T13:00:00Z)",
                        version=version)
            logging.debug("  requested initialisation time = '%s'", init_time)

            # Forecast valid time.
            valid_time = query.get('TIME')
            if valid_time is not None:
                try:
                    valid_time = parse_iso_datetime(valid_time)
                except ValueError:
                    return self.create_service_exception(
                        code="InvalidDimensionValue",
                        text="TIME has wrong format (needs to be 2005-08-29T13:00:00Z)",
                        version=version)
            logging.debug("  requested (valid) time = '%s'", valid_time)

            # Coordinate reference system.
            crs = query.get("CRS" if version == "1.3.0" else "SRS", 'EPSG:4326').lower()
            is_yx = version == "1.3.0" and crs.startswith("epsg") and int(crs[5:]) in axisorder_yx

            # Allow to request vertical sections via GetMap, if the specified CRS is of type "VERT:??".
            msg = None
            if crs.startswith('vert:logp'):
                mode = "getvsec"
            else:
                try:
                    get_projection_params(crs)
                except ValueError:
                    return self.create_service_exception(
                        code="InvalidSRS", text=f"The requested CRS '{crs}' is not supported.", version=version)
            logging.debug("  requested coordinate reference system = '%s'", crs)

            # Create a frameless figure (WMS) or one with title and legend
            # (MSS specific)? Default is WMS mode (frameless).
            noframe = query.get('FRAME', 'off').lower() == 'off'

            # Transparency.
            transparent = query.get('TRANSPARENT', 'false').lower() == 'true'
            if not transparent and index > 0:
                transparent = True
            if transparent:
                logging.debug("  requested transparent image")

            # Return format (image/png, text/xml, etc.).
            return_format = query.get('FORMAT', 'image/png').lower()
            logging.debug("  requested return format = '%s'", return_format)
            if return_format not in ["image/png", "text/xml"]:
                return self.create_service_exception(
                    code="InvalidFORMAT",
                    text=f"unsupported FORMAT: '{return_format}'",
                    version=version)

            # 3) Check GetMap/GetVSec-specific parameters and produce
            #    the image with the corresponding section driver.
            # =======================================================
            if mode == "getmap":
                # Check requested layer.
                if (dataset not in self.hsec_layer_registry) or (layer not in self.hsec_layer_registry[dataset]):
                    return self.create_service_exception(
                        code="LayerNotDefined",
                        text=f"Invalid LAYER '{dataset}.{layer}' requested",
                        version=version)

                # Check if the layer requires time information and if they are given.
                if init_time is None and self.hsec_layer_registry[dataset][layer].uses_inittime_dimension():
                    return self.create_service_exception(
                        code="MissingDimensionValue",
                        text="INIT_TIME not specified (use the DIM_INIT_TIME keyword)",
                        version=version)
                if valid_time is None and self.hsec_layer_registry[dataset][layer].uses_validtime_dimension():
                    return self.create_service_exception(
                        code="MissingDimensionValue",
                        text="TIME not specified",
                        version=version)

                # Check if the requested coordinate system is supported.
                if not self.hsec_layer_registry[dataset][layer].support_epsg_code(crs):
                    return self.create_service_exception(
                        code="InvalidSRS",
                        text=f"The requested CRS '{crs}' is not supported.",
                        version=version)

                # Bounding box.
                try:
                    if is_yx:
                        bbox = [float(v) for v in query.get('BBOX', '-90,-180,90,180').split(',')]
                        bbox = (bbox[1], bbox[0], bbox[3], bbox[2])
                    else:
                        bbox = [float(v) for v in query.get('BBOX', '-180,-90,180,90').split(',')]

                except ValueError:
                    return self.create_service_exception(text=f"Invalid BBOX: {query.get('BBOX')}", version=version)

                # Vertical level, if applicable.
                level = query.get('ELEVATION')
                level = float(level) if level is not None else None
                layer_datatypes = self.hsec_layer_registry[dataset][layer].required_datatypes()
                if level is None and any(_x in layer_datatypes for _x in ["pl", "al", "ml", "tl", "pv"]):
                    # Use the default value.
                    level = -1
                elif ("sfc" in layer_datatypes) and \
                        all(_x not in layer_datatypes for _x in ["pl", "al", "ml", "tl", "pv"]) and \
                        level is not None:
                    return self.create_service_exception(
                        text=f"ELEVATION argument not applicable for layer '{layer}'. Please omit this argument.",
                        version=version)

                plot_driver = self.hsec_drivers[dataset]
                try:
                    plot_driver.set_plot_parameters(self.hsec_layer_registry[dataset][layer], bbox=bbox, level=level,
                                                    crs=crs, init_time=init_time, valid_time=valid_time, style=style,
                                                    figsize=figsize, noframe=noframe, transparent=transparent,
                                                    return_format=return_format)
                    images.append(plot_driver.plot())
                except (IOError, ValueError) as ex:
                    logging.error("ERROR: %s %s", type(ex), ex)
                    logging.debug("%s", traceback.format_exc())
                    msg = "The data corresponding to your request is not available. Please check the " \
                          "times and/or levels you have specified.\n\n" \
                          f"Error message: '{ex}'"
                    return self.create_service_exception(text=msg, version=version)

            elif mode == "getvsec":
                # Vertical secton path.
                path = query.get("PATH")
                if path is None:
                    return self.create_service_exception(text="PATH not specified", version=version)
                try:
                    path = [float(v) for v in path.split(',')]
                    path = [[lat, lon] for lat, lon in zip(path[0::2], path[1::2])]
                except ValueError:
                    return self.create_service_exception(text=f"Invalid PATH: {path}", version=version)
                logging.debug("VSEC PATH: %s", path)

                # Check requested layers.
                if (dataset not in self.vsec_layer_registry) or (layer not in self.vsec_layer_registry[dataset]):
                    return self.create_service_exception(
                        code="LayerNotDefined",
                        text=f"Invalid LAYER '{dataset}.{layer}' requested",
                        version=version)

                # Check if the layer requires time information and if they are given.
                if self.vsec_layer_registry[dataset][layer].uses_inittime_dimension():
                    if init_time is None:
                        return self.create_service_exception(
                            code="MissingDimensionValue",
                            text="INIT_TIME not specified (use the DIM_INIT_TIME keyword)",
                            version=version)
                    if valid_time is None:
                        return self.create_service_exception(code="MissingDimensionValue",
                                                             text="TIME not specified",
                                                             version=version)

                # Bounding box (num interp. points, p_bot, num labels, p_top).
                try:
                    bbox = [float(v) for v in query.get("BBOX", "101,1050,10,180").split(",")]
                except ValueError:
                    return self.create_service_exception(text=f"Invalid BBOX: {query.get('BBOX')}", version=version)

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
                    images.append(plot_driver.plot())
                except (IOError, ValueError) as ex:
                    logging.error("ERROR: %s %s", type(ex), ex)
                    msg = "The data corresponding to your request is not available. Please check the " \
                          "times and/or path you have specified.\n\n" \
                          f"Error message: {ex}"
                    return self.create_service_exception(text=msg, version=version)

        # 4) Return the produced image.
        # =============================
        return squash_multiple_images(images), return_format


server = WMSServer()


@app.route('/')
@conditional_decorator(auth.login_required, mss_wms_settings.__dict__.get('enable_basic_http_authentication', False))
def application():
    try:
        # Request info
        query = CIMultiDict(request.args)
        # Processing
        # ToDo Refactor
        request_type = query.get('request')
        if request_type is None:  # request_type may *actually* be set to None
            request_type = ''
        request_type = request_type.lower()
        request_service = query.get('service', '')
        request_service = request_service.lower()
        request_version = query.get('version', '')

        url = request.url
        server_url = urllib.parse.urljoin(url, urllib.parse.urlparse(url).path)

        if (request_type in ('getcapabilities', 'capabilities') and
                request_service == 'wms' and request_version in ('1.1.1', '1.3.0', '')):
            return_data, return_format = server.get_capabilities(query, server_url)
        elif request_type in ('getmap', 'getvsec') and request_version in ('1.1.1', '1.3.0', ''):
            return_data, return_format = server.produce_plot(query, request_type)
        else:
            logging.debug("Request type '%s' is not valid.", request)
            raise RuntimeError("Request type is not valid.")

        res = make_response(return_data, 200)
        response_headers = [('Content-type', return_format), ('Content-Length', str(len(return_data)))]
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]

        return res

    except Exception as ex:
        logging.error("Unexpected error: %s: %s\nTraceback:\n%s",
                      type(ex), ex, traceback.format_exc())
        return render_template("/index.html")
