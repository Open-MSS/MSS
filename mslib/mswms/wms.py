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
import inspect
from xml.etree import ElementTree
from chameleon import PageTemplateLoader
from owslib.crs import axisorder_yx
from PIL import Image
import shutil

from flask import request, make_response, render_template
from flask_httpauth import HTTPBasicAuth
from multidict import CIMultiDict
from mslib.utils import conditional_decorator
from mslib.utils import parse_iso_datetime
from mslib.index import app_loader
from mslib.mswms.gallery_builder import add_image, write_html, write_doc_index, STATIC_LOCATION, DOCS_LOCATION

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
        register_linear_layers = []
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


def squash_multiple_xml(xml_strings):
    base = ElementTree.fromstring(xml_strings[0])
    for xml in xml_strings[1:]:
        tree = ElementTree.fromstring(xml)
        base.extend(tree)
    return ElementTree.tostring(base)


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

        self.lsec_drivers = {}
        for key in data_access_dict:
            self.lsec_drivers[key] = mss_plot_driver.LinearSectionDriver(
                data_access_dict[key])

        self.hsec_layer_registry = {}
        for layer, datasets in mss_wms_settings.register_horizontal_layers:
            self.register_hsec_layer(datasets, layer)

        self.vsec_layer_registry = {}
        for layer, datasets in mss_wms_settings.register_vertical_layers:
            self.register_vsec_layer(datasets, layer)

        self.lsec_layer_registry = {}
        if not hasattr(mss_wms_settings, "register_linear_layers"):
            logging.info("Since 4.0.0 MSS has support for linear layers in the mss_wms_settings.py.\n"
                         "Look at the documentation for an example "
                         "https://mss.readthedocs.io/en/stable/deployment.html#configuration-file-of-the-wms-server")
            mss_wms_settings.register_linear_layers = []
        for layer in mss_wms_settings.register_linear_layers:
            if len(layer) == 3:
                self.register_lsec_layer(layer[2], layer[1], layer_class=layer[0])
            elif len(layer) == 4:
                self.register_lsec_layer(layer[3], layer[1], layer[2], layer[0])
            else:
                self.register_lsec_layer(layer[1], layer_class=layer[0])

    def generate_gallery(self, create=False, clear=False, generate_code=False, sphinx=False, plot_list=None,
                         all_plots=False, url_prefix=""):
        """
        Iterates through all registered layers, draws their plots and puts them in the gallery
        """
        if mss_wms_settings.__file__:
            if all_plots:
                # Imports here due to some circular import issue if imported too soon
                from mslib.mswms import mpl_hsec_styles, mpl_vsec_styles, mpl_lsec_styles

                dataset = [next(iter(mss_wms_settings.data))]
                mss_wms_settings.register_horizontal_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_hsec_styles, inspect.isclass)
                    if not any(x in plot[0] or x in str(plot[1]) for x in ["Abstract", "Target", "fnord"])
                ]
                mss_wms_settings.register_vertical_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_vsec_styles, inspect.isclass)
                    if not any(x in plot[0] or x in str(plot[1]) for x in ["Abstract", "Target", "fnord"])
                ]
                mss_wms_settings.register_linear_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_lsec_styles, inspect.isclass)
                ]
                self.__init__()

            location = DOCS_LOCATION if sphinx else STATIC_LOCATION
            if clear and os.path.exists(os.path.join(location, "plots")):
                shutil.rmtree(os.path.join(location, "plots"))
            if os.path.exists(os.path.join(location, "code")):
                shutil.rmtree(os.path.join(location, "code"))
            if os.path.exists(os.path.join(location, "plots.html")):
                os.remove(os.path.join(location, "plots.html"))

            if not (create or generate_code or all_plots or plot_list):
                return

            if not plot_list:
                plot_list = [[self.lsec_drivers, self.lsec_layer_registry],
                             [self.vsec_drivers, self.vsec_layer_registry],
                             [self.hsec_drivers, self.hsec_layer_registry]]

            for driver, registry in plot_list:
                multiple_datasets = len(driver) > 1
                for dataset in driver:
                    plot_driver = driver[dataset]
                    if dataset not in registry:
                        continue
                    for plot in registry[dataset]:
                        plot_object = registry[dataset][plot]
                        l_type = "Linear" if driver == self.lsec_drivers else \
                            "Side" if driver == self.vsec_drivers else "Top"

                        try:
                            if not os.path.exists(os.path.join(location, "plots",
                                                               f"{l_type}_{plot_object.name}.png")):
                                # Plot doesn't already exist, generate it
                                file_type = next((field[0] for field in plot_object.required_datafields
                                                  if field[0] != "sfc"), "sfc")
                                init_time = plot_driver.get_init_times()[-1]
                                valid_time = plot_driver.get_valid_times(plot_object.required_datafields[0][1],
                                                                         file_type, init_time)[-1]
                                style = plot_object.styles[0][0] if plot_object.styles else None
                                kwargs = {"plot_object": plot_object,
                                          "init_time": init_time,
                                          "valid_time": valid_time}
                                if driver == self.lsec_drivers:
                                    plot_driver.set_plot_parameters(**kwargs, lsec_path=[[0, 0, 20000], [1, 1, 20000]],
                                                                    lsec_numpoints=201, lsec_path_connection="linear")
                                    path = [[min(plot_driver.lat_data), min(plot_driver.lon_data), 20000],
                                            [max(plot_driver.lat_data), max(plot_driver.lon_data), 20000]]
                                    plot_driver.update_plot_parameters(lsec_path=path)
                                elif driver == self.vsec_drivers:
                                    plot_driver.set_plot_parameters(**kwargs, vsec_path=[[0, 0], [1, 1]],
                                                                    vsec_numpoints=201, figsize=[800, 600],
                                                                    vsec_path_connection="linear", style=style,
                                                                    noframe=False, bbox=[101, 1050, 10, 180])
                                    path = [[min(plot_driver.lat_data), min(plot_driver.lon_data)],
                                            [max(plot_driver.lat_data), max(plot_driver.lon_data)]]
                                    plot_driver.update_plot_parameters(vsec_path=path)
                                elif driver == self.hsec_drivers:
                                    elevations = plot_object.get_elevations()
                                    elevation = float(elevations[len(elevations) // 2]) if len(elevations) > 0 else None
                                    plot_driver.set_plot_parameters(**kwargs, noframe=False, figsize=[800, 600],
                                                                    crs="EPSG:4326", style=style,
                                                                    bbox=[-15, 35, 30, 65],
                                                                    level=elevation)
                                    bbox = [min(plot_driver.lon_data), min(plot_driver.lat_data),
                                            max(plot_driver.lon_data), max(plot_driver.lat_data)]
                                    # Create square bbox for better images
                                    # if abs(bbox[0] - bbox[2]) > abs(bbox[1] - bbox[3]):
                                    #     bbox[2] = bbox[0] + abs(bbox[1] - bbox[3])
                                    # else:
                                    #     bbox[3] = bbox[1] + abs(bbox[0] - bbox[2])
                                    plot_driver.update_plot_parameters(bbox=bbox)
                                add_image(plot_driver.plot(), plot_object, generate_code, sphinx, url_prefix=url_prefix,
                                          dataset=dataset if multiple_datasets else "")
                            else:
                                # Plot already exists, skip generation
                                add_image(None, plot_object, generate_code, sphinx, url_prefix=url_prefix,
                                          dataset=dataset if multiple_datasets else "")

                        except Exception as e:
                            traceback.print_exc()
                            logging.error("%s %s %s", plot_object.name, type(e), e)
            write_html(sphinx)
            if sphinx and generate_code:
                write_doc_index()

    def register_hsec_layer(self, datasets, layer_class):
        """
        Register horizontal section layer in internal dict of layers.

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
        """
        Register vertical section layer in internal dict of layers.

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

    def register_lsec_layer(self, datasets, variable=None, filetype="ml", layer_class=None):
        """
        Register linear section layer in internal dict of layers.

        See register_hsec_layer() for further information.
        """
        # Loop over all provided dataset names. Create an instance of the
        # provided layer class for all datasets and register the layer
        # instances with the datasets.
        for dataset in datasets:
            try:
                if variable:
                    layer = layer_class(self.lsec_drivers[dataset], variable, filetype)
                else:
                    layer = layer_class(self.lsec_drivers[dataset])
            except KeyError as ex:
                logging.debug("ERROR: %s %s", type(ex), ex)
                continue
            logging.debug("registering linear section layer '%s' with dataset '%s'", layer.name, dataset)
            # Check if the current dataset has already been registered. If
            # not, check whether a suitable driver is available.
            if dataset not in self.lsec_layer_registry:
                if dataset in self.lsec_drivers:
                    self.lsec_layer_registry[dataset] = {}
                else:
                    raise ValueError("dataset '%s' not available", dataset)
            self.lsec_layer_registry[dataset][layer.name] = layer

    def create_service_exception(self, code=None, text="", version="1.3.0"):
        """
        Create a service exception XML from the XML template defined above.

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

        # Linear Layers
        lsec_layers = []
        for dataset in self.lsec_layer_registry:
            for layer in self.lsec_layer_registry[dataset].values():
                if layer.uses_inittime_dimension() and len(layer.get_init_times()) == 0:
                    logging.error("layer %s/%s has no init times!", layer, dataset)
                    continue
                if layer.uses_validtime_dimension() and len(layer.get_all_valid_times()) == 0:
                    logging.error("layer %s/%s has no valid times!", layer, dataset)
                    continue
                lsec_layers.append((dataset, layer))

        settings = mss_wms_settings.__dict__
        return_data = template(hsec_layers=hsec_layers, vsec_layers=vsec_layers, lsec_layers=lsec_layers,
                               server_url=server_url,
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
            style = styles[index] if len(styles) > index else None
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
            elif crs.startswith("line:1"):
                mode = "getlsec"
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

                draw_verticals = query.get("DRAWVERTICALS", "false").lower() == "true"

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
                                                    draw_verticals=draw_verticals,
                                                    transparent=transparent,
                                                    return_format=return_format)
                    images.append(plot_driver.plot())
                except (IOError, ValueError) as ex:
                    logging.error("ERROR: %s %s", type(ex), ex)
                    msg = "The data corresponding to your request is not available. Please check the " \
                          "times and/or path you have specified.\n\n" \
                          f"Error message: {ex}.\n" \
                          "Hint: Check used waypoints."
                    return self.create_service_exception(text=msg, version=version)

            elif mode == "getlsec":
                if return_format != "text/xml":
                    return self.create_service_exception(
                        code="InvalidFORMAT",
                        text=f"unsupported FORMAT: '{return_format}'",
                        version=version)

                # Linear section path.
                path = query.get("PATH")
                if path is None:
                    return self.create_service_exception(text="PATH not specified", version=version)
                try:
                    path = [float(v) for v in path.split(',')]
                    path = [[lat, lon, alt] for lat, lon, alt in zip(path[0::3], path[1::3], path[2::3])]
                except ValueError:
                    return self.create_service_exception(text=f"Invalid PATH: {path}", version=version)
                logging.debug("LSEC PATH: %s", path)

                # Check requested layers.
                if (dataset not in self.lsec_layer_registry) or (layer not in self.lsec_layer_registry[dataset]):
                    return self.create_service_exception(
                        code="LayerNotDefined",
                        text=f"Invalid LAYER '{dataset}.{layer}' requested",
                        version=version)

                # Check if the layer requires time information and if they are given.
                if self.lsec_layer_registry[dataset][layer].uses_inittime_dimension():
                    if init_time is None:
                        return self.create_service_exception(
                            code="MissingDimensionValue",
                            text="INIT_TIME not specified (use the DIM_INIT_TIME keyword)",
                            version=version)
                    if valid_time is None:
                        return self.create_service_exception(code="MissingDimensionValue",
                                                             text="TIME not specified",
                                                             version=version)

                # Bounding box (num interp. points).
                try:
                    bbox = float(query.get("BBOX", "101"))
                except ValueError:
                    return self.create_service_exception(text=f"Invalid BBOX: {query.get('BBOX')}", version=version)

                plot_driver = self.lsec_drivers[dataset]
                try:
                    plot_driver.set_plot_parameters(plot_object=self.lsec_layer_registry[dataset][layer],
                                                    lsec_path=path,
                                                    lsec_numpoints=bbox,
                                                    lsec_path_connection="greatcircle",
                                                    init_time=init_time,
                                                    valid_time=valid_time,
                                                    bbox=bbox)
                    images.append(plot_driver.plot())
                except (IOError, ValueError) as ex:
                    logging.error("ERROR: %s %s", type(ex), ex)
                    msg = "The data corresponding to your request is not available. Please check the " \
                          "times and/or path you have specified.\n\n" \
                          f"Error message: {ex}.\n" \
                          "Hint: Check used waypoints."
                    return self.create_service_exception(text=msg, version=version)

        # 4) Return the produced image.
        # =============================
        if len(layers) > 1:
            if "image" in return_format:
                return squash_multiple_images(images), return_format
            elif "xml" in return_format:
                return squash_multiple_xml(images), return_format
            else:
                raise RuntimeError(f"Unexpected format error: {return_format}")
        else:
            return images[0], return_format


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
        elif request_type in ('getmap', 'getvsec', 'getlsec') and request_version in ('1.1.1', '1.3.0', ''):
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
        # without query parameter show index page
        query = request.args
        if len(query) == 0:
            return render_template("/index.html")

        # communicate request errors back to client user
        logging.error("Unexpected error: %s: %s\nTraceback:\n%s",
                      type(ex), ex, traceback.format_exc())
        error_message = "{}: {}\n".format(type(ex), ex)
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(error_message)))]
        res = make_response(error_message, 404)
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]
        return res
