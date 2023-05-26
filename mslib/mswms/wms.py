# -*- coding: utf-8 -*-
"""

    mslib.mswms.wms
    ~~~~~~~~~~~~~~~

    WSGI module for MSS WMS server that provides access to ECMWF forecast data.

    The module implements a Web Map Service 1.1.1/1.3.0 interface to provide forecast data
    from numerical weather predictions to the Mission Support User Interface.
    Supported operations are GetCapabilities and GetMap for (WMS 1.1.1/1.3.0 compliant)
    maps and (non-compliant) vertical sections.

    1) Configure the WMS server by modifying the settings in mswms_settings.py
    (address, products that shall be offered, ..).

    2) If you want to define new visualisation styles, the files to put them
    are mpl_hsec_styles.py and mpl_vsec_styles for maps and vertical sections,
    respectively.

    For more information on WMS, see http://www.opengeospatial.org/standards/wms

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr), Omar Qunsul (oq)
    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

import glob
import os
import io
import inspect
import logging
import shutil
import tempfile
import traceback
import urllib.parse

from xml.etree import ElementTree
from chameleon import PageTemplateLoader
from owslib.crs import axisorder_yx
from PIL import Image
import numpy as np
from flask import request, make_response, render_template
from flask_httpauth import HTTPBasicAuth

from multidict import CIMultiDict
from mslib.utils import conditional_decorator
from mslib.utils.time import parse_iso_datetime
from mslib.index import create_app
from mslib.mswms.gallery_builder import add_image, write_html, add_levels, add_times, \
    write_doc_index, write_code_pages, STATIC_LOCATION, DOCS_LOCATION

# Flask basic auth's documentation
# https://flask-basicauth.readthedocs.io/en/latest/#flask.ext.basicauth.BasicAuth.check_credentials

app = create_app(__name__)
auth = HTTPBasicAuth()

realm = 'Mission Support Web Map Service'
app.config['realm'] = realm


class default_mswms_settings:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    xml_template_location = os.path.join(base_dir, "xml_templates")
    service_name = "OGC:WMS"
    service_title = "Mission Support System Web Map Service"
    service_abstract = ""
    service_contact_person = ""
    service_contact_organisation = ""
    service_contact_position = ""
    service_address_type = ""
    service_address = ""
    service_city = ""
    service_state_or_province = ""
    service_post_code = ""
    service_country = ""
    service_fees = ""
    service_email = ""
    service_access_constraints = "This service is intended for research purposes only."
    register_horizontal_layers = []
    register_vertical_layers = []
    register_linear_layers = []
    data = {}
    enable_basic_http_authentication = False
    __file__ = None


mswms_settings = default_mswms_settings()

try:
    import mswms_settings as user_settings
    mswms_settings.__dict__.update(user_settings.__dict__)
except ImportError as ex:
    logging.warning("Couldn't import mswms_settings (ImportError:'%s'), Using dummy config.", ex)

try:
    import mswms_auth
except ImportError as ex:
    logging.warning("Couldn't import mswms_auth (ImportError:'{%s), creating dummy config.", ex)

    class mswms_auth:
        allowed_users = [("mswms", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None

if mswms_settings.enable_basic_http_authentication:
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    import hashlib

    def authfunc(username, password):
        for u, p in mswms_auth.allowed_users:
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
from mslib.utils.coordinate import get_projection_params

# Logging the Standard Output, which will be added to the Apache Log Files
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(funcName)19s || %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

# Chameleon XMl template
templates = PageTemplateLoader(mswms_settings.xml_template_location)


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


class WMSServer:

    def __init__(self):
        """
        init method for wms server
        """
        data_access_dict = mswms_settings.data

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
        for layer, datasets in mswms_settings.register_horizontal_layers:
            self.register_hsec_layer(datasets, layer)

        self.vsec_layer_registry = {}
        for layer, datasets in mswms_settings.register_vertical_layers:
            self.register_vsec_layer(datasets, layer)

        self.lsec_layer_registry = {}
        if not hasattr(mswms_settings, "register_linear_layers"):
            logging.info("Since 4.0.0 MSS has support for linear layers in the mswms_settings.py.\n"
                         "Look at the documentation for an example "
                         "https://mss.readthedocs.io/en/stable/deployment.html#configuration-file-of-the-wms-server")
            mswms_settings.register_linear_layers = []
        for layer in mswms_settings.register_linear_layers:
            if len(layer) == 3:
                self.register_lsec_layer(layer[2], layer[1], layer_class=layer[0])
            elif len(layer) == 4:
                self.register_lsec_layer(layer[3], layer[1], layer[2], layer[0])
            else:
                self.register_lsec_layer(layer[1], layer_class=layer[0])

    def generate_gallery(self, create=False, clear=False, generate_code=False, sphinx=False, plot_list=None,
                         all_plots=False, url_prefix="", levels="", itimes="", vtimes="", simple_naming=False,
                         plot_types=None):
        """
        Iterates through all registered layers, draws their plots and puts them in the gallery
        """
        if mswms_settings.__file__:
            if all_plots:
                # Imports here due to some circular import issue if imported too soon
                from mslib.mswms import mpl_hsec_styles, mpl_vsec_styles, mpl_lsec_styles

                dataset = [next(iter(mswms_settings.data))]
                mswms_settings.register_horizontal_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_hsec_styles, inspect.isclass)
                    if plot[0] != "HS_GenericStyle" and
                    not any(x in plot[0] or x in str(plot[1]) for x in ["Abstract", "Target", "fnord"])
                ]
                mswms_settings.register_vertical_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_vsec_styles, inspect.isclass)
                    if plot[0] != "VS_GenericStyle" and
                    not any(x in plot[0] or x in str(plot[1]) for x in ["Abstract", "Target", "fnord"])
                ]
                mswms_settings.register_linear_layers = [
                    (plot[1], dataset) for plot in inspect.getmembers(mpl_lsec_styles, inspect.isclass)
                ]
                self.__init__()

            if not (create or generate_code or all_plots or plot_list):
                return

            tmp_path = tempfile.mkdtemp()
            path = DOCS_LOCATION if sphinx else STATIC_LOCATION

            if plot_list is None:
                plot_list = [[self.lsec_drivers, self.lsec_layer_registry],
                             [self.vsec_drivers, self.vsec_layer_registry],
                             [self.hsec_drivers, self.hsec_layer_registry]]

            # Iterate through all plots of all datasets, create the plot and build the gallery with it
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
                            file_types = [field[0] for field in plot_object.required_datafields
                                          if field[0] != "sfc"]
                            file_type = file_types[0] if file_types else "sfc"

                            # All specified init times, or the latest if empty, or all if "all",
                            # or None if there are no init times
                            init_times = [parse_iso_datetime(itime) if isinstance(itime, str) else itime
                                          for itime in (itimes.split(",") if itimes != "all" and itimes != "" else
                                                        plot_driver.get_init_times() if itimes == "all" else
                                                        [plot_driver.get_init_times()[-1]])] or [None]

                            for itime in sorted(init_times):
                                if itime and plot_driver.get_init_times() and itime not in plot_driver.get_init_times():
                                    logging.warning("Requested itime %s not present for "
                                                    "%s %s! itimes present: "
                                                    "%s", itime, dataset, plot_object.name, plot_driver.get_init_times()
                                                    )
                                    continue
                                elif not plot_driver.get_init_times():
                                    itime = None

                                try:
                                    # All valid times for the specific init time
                                    i_vtimes = plot_driver.get_valid_times(plot_object.required_datafields[0][1],
                                                                           file_type, itime)
                                except IndexError:
                                    # ToDo fix demodata for sfc
                                    logging.debug("plot_object.required_datafields incomplete"
                                                  " for filetype: %s in dataset: %s for l_type: %s",
                                                  file_type, dataset, l_type)
                                    continue

                                # All specified valid times, or the latest if empty, or all if "all",
                                # or None if there are no valid times for the init time
                                valid_times = [parse_iso_datetime(vtime) if isinstance(vtime, str) else vtime
                                               for vtime in (vtimes.split(",") if vtimes != "all" and vtimes != "" else
                                                             i_vtimes if vtimes == "all" else [i_vtimes[-1]])] or [None]

                                for vtime in sorted(valid_times):
                                    if vtime and i_vtimes and vtime not in i_vtimes:
                                        logging.warning("Requested vtime %s at %s not present for "
                                                        "%s %s! vtimes present: %s", vtime, itime, dataset,
                                                        plot_object.name, i_vtimes)
                                        continue
                                    elif not i_vtimes:
                                        vtime = None

                                    style = plot_object.styles[0][0] if plot_object.styles else None
                                    kwargs = {"plot_object": plot_object,
                                              "init_time": itime,
                                              "valid_time": vtime}
                                    filename = f"{l_type}_{dataset if multiple_datasets else ''}{plot_object.name}-" \
                                               + f"Noneit{itime}vt{vtime}".replace(" ", "_").replace(":", "_")\
                                                                          .replace("-", "_")

                                    exists = (not clear) and os.path.exists(
                                        os.path.join(path, "plots", filename + ".png"))

                                    if driver == self.lsec_drivers and not exists:
                                        plot_driver.set_plot_parameters(**kwargs,
                                                                        lsec_path=[[0, 0, 20000], [1, 1, 20000]],
                                                                        lsec_numpoints=201,
                                                                        lsec_path_connection="linear",
                                                                        mime_type="text/xml")
                                        lon_data = np.rad2deg(np.unwrap(np.deg2rad(plot_driver.lon_data)))
                                        lpath = [[min(plot_driver.lat_data), min(lon_data), 20000],
                                                 [max(plot_driver.lat_data), max(lon_data), 20000]]
                                        plot_driver.update_plot_parameters(lsec_path=lpath)

                                    elif driver == self.vsec_drivers and not exists:
                                        plot_driver.set_plot_parameters(**kwargs, vsec_path=[[0, 0], [1, 1]],
                                                                        vsec_numpoints=201, figsize=[800, 600],
                                                                        vsec_path_connection="linear", style=style,
                                                                        noframe=False, bbox=[101, 1050, 10, 180],
                                                                        mime_type="image/png")
                                        lon_data = np.rad2deg(np.unwrap(np.deg2rad(plot_driver.lon_data)))
                                        lpath = [[min(plot_driver.lat_data), min(lon_data)],
                                                 [max(plot_driver.lat_data), max(lon_data)]]
                                        plot_driver.update_plot_parameters(vsec_path=lpath)

                                    elif driver == self.hsec_drivers:
                                        elevations = plot_object.get_elevations()
                                        elevation = float(elevations[len(elevations) // 2]) if len(elevations) > 0 \
                                            else None
                                        plot_driver.set_plot_parameters(**kwargs, noframe=False, figsize=[800, 600],
                                                                        crs="EPSG:4326", style=style,
                                                                        bbox=[-15, 35, 30, 65],
                                                                        level=elevation,
                                                                        mime_type="image/png")
                                        lon_data = np.rad2deg(np.unwrap(np.deg2rad(plot_driver.lon_data)))
                                        bbox = [min(lon_data), min(plot_driver.lat_data),
                                                max(lon_data), max(plot_driver.lat_data)]
                                        vert_units = plot_driver.vert_units
                                        plot_driver.update_plot_parameters(bbox=bbox)

                                        # All specified levels, or the mid if empty, or all if "all",
                                        # or None if there are no levels
                                        rendered_levels = [float(elev) if elev else elev for elev in
                                                           (levels.split(",") if (levels != "all" and levels != "") else
                                                            elevations if levels == "all" else [elevation])] or [None]

                                        for level in sorted(rendered_levels):
                                            if level and elevations and level \
                                                    not in [float(elev) for elev in elevations]:
                                                logging.warning("Requested level %s not present for "
                                                                "%s %s! Levels present: "
                                                                "%s", level, dataset, plot_object.name, elevations)
                                                continue
                                            elif not elevations:
                                                level = None

                                            plot_driver.update_plot_parameters(level=level)

                                            # filename is different for top layers, so needs a redefine
                                            filename = f"{l_type}_{dataset if multiple_datasets else ''}" \
                                                       f"{plot_object.name}-" + \
                                                       f"{level}{vert_units}it{itime}vt{vtime}".replace(" ", "_")\
                                                                                               .replace(":", "_")\
                                                                                               .replace("-", "_")
                                            exists = (not clear) and os.path.exists(
                                                os.path.join(path, "plots", filename + ".png"))

                                            add_image(tmp_path, None if exists else plot_driver.plot(), plot_object,
                                                      generate_code, sphinx, url_prefix=url_prefix,
                                                      dataset=dataset if multiple_datasets else "", level=f"{level}" +
                                                                                                f"{vert_units}",
                                                      itime=str(itime), vtime=str(vtime), simple_naming=simple_naming,
                                                      plot_types=plot_types)
                                            if level:
                                                add_levels([f"{level} {vert_units}"], vert_units)
                                            else:
                                                add_levels(["None None"], "None")

                                            add_times(itime, [vtime])
                                        continue

                                    add_image(
                                        tmp_path,
                                        None if exists else plot_driver.plot(), plot_object, generate_code,
                                        sphinx, url_prefix=url_prefix,
                                        dataset=dataset if multiple_datasets else "", itime=str(itime),
                                        vtime=str(vtime), simple_naming=simple_naming, plot_types=plot_types)
                                    add_times(itime, [vtime])

                        except Exception as e:
                            traceback.print_exc()
                            logging.error("%s %s %s", plot_object.name, type(e), e)

            write_html(tmp_path, sphinx, plot_types=plot_types)
            if generate_code:
                write_code_pages(tmp_path, sphinx, url_prefix)
                if sphinx:
                    write_doc_index(tmp_path)

            if clear and os.path.exists(os.path.join(path, "plots")):
                shutil.rmtree(os.path.join(path, "plots"))
            if os.path.exists(os.path.join(path, "plots")):
                for fn in glob.glob(os.path.join(tmp_path, "plots", "*")):
                    if not os.path.exists(os.path.join(path, "plots", os.path.basename(fn))):
                        shutil.move(fn, os.path.join(path, "plots"))
            else:
                shutil.move(os.path.join(tmp_path, "plots"), path)
            if os.path.exists(os.path.join(path, "code")):
                shutil.rmtree(os.path.join(path, "code"))
            if os.path.exists(os.path.join(tmp_path, "code")):
                shutil.move(os.path.join(tmp_path, "code"), path)
            if os.path.exists(os.path.join(path, "plots.html")):
                os.remove(os.path.join(path, "plots.html"))
            if os.path.exists(os.path.join(tmp_path, "plots.html")):
                shutil.move(os.path.join(tmp_path, "plots.html"), path)
            shutil.rmtree(tmp_path)

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
            if layer.name in self.hsec_layer_registry[dataset]:
                raise ValueError(f"new layer is already registered? dataset={dataset} layer.name={layer.name} "
                                 f"new={layer} old={self.hsec_layer_registry[dataset][layer.name]}")
            if layer.name == "HS_GenericStyle":
                raise ValueError(f"problem in configuration for dataset={dataset}. We found layer.name={layer.name}"
                                 f"  The class HS_GenericStyle should never be used.")
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
            if layer.name in self.vsec_layer_registry[dataset]:
                raise ValueError(f"new layer is already registered? dataset={dataset} layer.name={layer.name} "
                                 f"new={layer} old={self.vsec_layer_registry[dataset][layer.name]}")
            if layer.name == "VS_GenericStyle":
                raise ValueError(f"problem in configuration for dataset={dataset}. We found layer.name={layer.name}"
                                 f" The class VS_GenericStyle should never be used.")
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
            if layer.name in self.lsec_layer_registry[dataset]:
                raise ValueError(f"new layer is already registered? dataset={dataset} layer.name={layer.name} "
                                 f"new={layer} old={self.lsec_layer_registry[dataset][layer.name]}")
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
        data_access_dict = mswms_settings.data

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

        return_data = template(hsec_layers=hsec_layers, vsec_layers=vsec_layers, lsec_layers=lsec_layers,
                               server_url=server_url,
                               service_name=mswms_settings.service_name,
                               service_title=mswms_settings.service_title,
                               service_abstract=mswms_settings.service_abstract,
                               service_contact_person=mswms_settings.service_contact_person,
                               service_contact_organisation=mswms_settings.service_contact_organisation,
                               service_contact_position=mswms_settings.service_contact_position,
                               service_email=mswms_settings.service_email,
                               service_address_type=mswms_settings.service_address_type,
                               service_address=mswms_settings.service_address,
                               service_city=mswms_settings.service_city,
                               service_state_or_province=mswms_settings.service_state_or_province,
                               service_post_code=mswms_settings.service_post_code,
                               service_country=mswms_settings.service_country,
                               service_fees=mswms_settings.service_fees,
                               service_access_constraints=mswms_settings.service_access_constraints)
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
            mime_type = query.get('FORMAT', 'image/png').lower()
            logging.debug("  requested return format = '%s'", mime_type)
            if mime_type not in ["image/png", "text/xml"]:
                return self.create_service_exception(
                    code="InvalidFORMAT",
                    text=f"unsupported FORMAT: '{mime_type}'",
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
                from mslib.utils.netCDF4tools import VERTICAL_AXIS
                if level is None and any(_x in layer_datatypes for _x in VERTICAL_AXIS):
                    # Use the default value.
                    level = -1
                elif ("sfc" in layer_datatypes) and \
                        all(_x not in layer_datatypes for _x in VERTICAL_AXIS) and \
                        level is not None:
                    return self.create_service_exception(
                        text=f"ELEVATION argument not applicable for layer '{layer}'. Please omit this argument.",
                        version=version)

                plot_driver = self.hsec_drivers[dataset]
                try:
                    plot_driver.set_plot_parameters(self.hsec_layer_registry[dataset][layer], bbox=bbox, level=level,
                                                    crs=crs, init_time=init_time, valid_time=valid_time, style=style,
                                                    figsize=figsize, noframe=noframe, transparent=transparent,
                                                    mime_type=mime_type)
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
                                                    mime_type=mime_type)
                    images.append(plot_driver.plot())
                except (IOError, ValueError) as ex:
                    logging.error("ERROR: %s %s", type(ex), ex)
                    msg = "The data corresponding to your request is not available. Please check the " \
                          "times and/or path you have specified.\n\n" \
                          f"Error message: {ex}.\n" \
                          "Hint: Check used waypoints."
                    return self.create_service_exception(text=msg, version=version)

            elif mode == "getlsec":
                if mime_type != "text/xml":
                    return self.create_service_exception(
                        code="InvalidFORMAT",
                        text=f"unsupported FORMAT: '{mime_type}'",
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
                                                    bbox=bbox,
                                                    mime_type=mime_type)
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
            if "image" in mime_type:
                return squash_multiple_images(images), mime_type
            elif "xml" in mime_type:
                return squash_multiple_xml(images), mime_type
            else:
                raise RuntimeError(f"Unexpected format error: {mime_type}")
        else:
            return images[0], mime_type


server = WMSServer()


@app.route('/')
@conditional_decorator(auth.login_required, mswms_settings.enable_basic_http_authentication)
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
            return_data, mime_type = server.get_capabilities(query, server_url)
        elif request_type in ('getmap', 'getvsec', 'getlsec') and request_version in ('1.1.1', '1.3.0', ''):
            return_data, mime_type = server.produce_plot(query, request_type)
        else:
            logging.debug("Request type '%s' is not valid.", request)
            raise RuntimeError("Request type is not valid.")

        res = make_response(return_data, 200)
        response_headers = [('Content-type', mime_type), ('Content-Length', str(len(return_data)))]
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
