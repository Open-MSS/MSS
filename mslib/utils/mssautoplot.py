"""

    mslib.utils.mssautoplot
    ~~~~~~~~~~~~~~~~~~~~~~~

    A CLI tool to create for instance a number of the same plots
    for several flights or several forecast steps

    This file is part of MSS.

    :copyright: Copyright 2022 Sreelakshmi Jayarajan
    :copyright: Copyright 2022-2024 by the MSS team, see AUTHORS.
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

import os
import io
import re
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
import click
import defusedxml.ElementTree as etree
import PIL.Image
import matplotlib
from slugify import slugify
from fs import open_fs

import mslib
import mslib.utils
import mslib.msui
import mslib.msui.mpl_map
import mslib.utils.auth
import mslib.utils.qt
import mslib.utils.thermolib
from mslib.utils.config import config_loader, read_config_file
from mslib.utils.units import units
from mslib.msui.wms_control import MSUIWebMapService
from mslib.msui import constants
from mslib.msui import mpl_qtwidget as qt
from mslib.msui import mpl_pathinteractor as mpath
from mslib.msui import flighttrack as ft
from mslib.utils import config as conf
from mslib.utils.get_projection_params import get_projection_params
from mslib.utils.auth import get_auth_from_url_and_name
from mslib.utils.loggerdef import configure_mpl_logger
from mslib.utils.verify_user_token import verify_user_token


TEXT_CONFIG = {
    "bbox": dict(boxstyle="round", facecolor="white", alpha=0.5, edgecolor="none"), "fontweight": "bold",
    "zorder": 4, "fontsize": 6, "clip_on": True}

mpl_logger = configure_mpl_logger()


def load_from_ftml(filename):
    """Load a flight track from an XML file at <filename>.
    """
    _dirname, _name = os.path.split(filename)
    _fs = open_fs(_dirname)
    datasource = _fs.readtext(_name)
    wp_list = ft.load_from_xml_data(datasource)
    now = datetime.now()
    for wp in wp_list:
        wp.utc_time = now
    data_list = [
        (wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_list]
    return data_list, wp_list


def load_from_operation(op_name, msc_url, msc_auth_password, username, password):
    """
    Method to load data from an operation in MSColab.

    Parameters:
    :op_name: Name of the operation to load data from
    :msc_url: URL of the MS Colab server
    :msc_auth_password: Password for MS Colab authentication
    :username: Username for authentication
    :password: Password for authentication

    Returns:
    Tuple containing a list of data points and a list of Waypoints if successful, None otherwise
    """
    data = {
        "email": username,
        "password": password
    }
    session = requests.Session()
    msc_auth = ("mscolab", msc_auth_password)
    session.auth = msc_auth
    session.headers.update({'x-test': 'true'})
    # ToDp fix config_loader it gets a list of two times the entry
    response = session.get(urljoin(msc_url, 'status'), timeout=tuple(config_loader(dataset="MSCOLAB_timeout")[0]))
    session.close()
    if response.status_code == 401:
        logging.error("Error", 'Server authentication data were incorrect.')
    elif response.status_code == 200:
        session = requests.Session()
        session.auth = msc_auth
        session.headers.update({'x-test': 'true'})
        url = urljoin(msc_url, "token")
        try:
            # ToDp fix config_loader it gets a list of two times the entry
            response = session.post(url, data=data, timeout=tuple(config_loader(dataset="MSCOLAB_timeout")[0]))
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            logging.error("unexpected error: %s %s %s", type(ex), url, ex)
            return
        if response.text != "False":
            _json = json.loads(response.text)
            token = _json["token"]
            msc_url = url
            op_id = get_op_id(msc_url=msc_url, token=token, op_name=op_name)
            xml_data = get_xml_data(msc_url=msc_url, token=token, op_id=op_id)
            wp_list = ft.load_from_xml_data(xml_data)
            now = datetime.now()
            for wp in wp_list:
                wp.utc_time = now
            data_list = [
                (wp.lat, wp.lon, wp.flightlevel, wp.location, wp.comments) for wp in wp_list]
            return data_list, wp_list


def get_xml_data(msc_url, token, op_id):
    """

    Parameters:
        :msc_url: The URL of the MSColab Server
        :token: The user's token for authentication
        :op_id: The id of the operation to retrieve

    Returns:
        str: The content of the XML data retrieved from the server

    """
    if verify_user_token(msc_url, token):
        data = {
            "token": token,
            "op_id": op_id
        }
        url = urljoin(msc_url, "get_operation_by_id")
        r = requests.get(url, data=data)
        if r.text != "False":
            xml_content = json.loads(r.text)["content"]
            return xml_content


def get_op_id(msc_url, token, op_name):
    """
    gets the operation id of the given operation name

    Parameters:
        :msc_url: The URL of the MSColab server
        :token: The user token for authentication
        :op_name:: The name of the operation to retrieve op_id for

    Returns:
        :op_id: The op_id of the operation with the specified name
    """
    logging.debug('get_recent_op_id')
    if verify_user_token(msc_url, token):
        """
        get most recent operation's op_id
        """
        skip_archived = config_loader(dataset="MSCOLAB_skip_archived_operations")
        data = {
            "token": token,
            "skip_archived": skip_archived
        }
        url = urljoin(msc_url, "operations")
        r = requests.get(url, data=data)
        if r.text != "False":
            _json = json.loads(r.text)
            operations = _json["operations"]
            for op in operations:
                if op["path"] == op_name:
                    return op["op_id"]


class Plotting:
    def __init__(self, cpath, msc_url=None, msc_auth_password=None, username=None, password=None, pdlg=None, raw=False):
        """
        Initialize the Plotting object with the provided parameters.

        Parameters:
        :cpath: Path to the configuration file
        :msc_url: URL for MSColab service
        :msc_auth_password: Authentication password for MSColab service
        :username: User's username
        :password: User's password
        """
        read_config_file(cpath)
        self.pdlg = pdlg
        self.config = config_loader()
        self.num_interpolation_points = self.config["num_interpolation_points"]
        self.num_labels = self.config["num_labels"]
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.bbox = None
        flight = self.config["automated_plotting_flights"][0][0]
        section = self.config["automated_plotting_flights"][0][1]
        filename = self.config["automated_plotting_flights"][0][3]
        if self.__class__.__name__ == "TopViewPlotting":
            try:
                self.params = get_projection_params(self.config["predefined_map_sections"][section]["CRS"].lower())
            except KeyError as e:
                print(e)
                raise SystemExit("Invalid SECTION and/or CRS")
            self.params["basemap"].update(self.config["predefined_map_sections"][section]["map"])
            self.bbox_units = self.params["bbox"]
            self.layout = self.config["layout"]["topview"]
        if self.__class__.__name__ == "SideViewPlotting":
            self.layout = self.config["layout"]["sideview"]
        if self.__class__.__name__ == "LinearViewPlotting":
            self.layout = self.config["layout"]["linearview"]
        if filename != "" and filename == flight:
            self.read_operation(flight, msc_url, msc_auth_password, username, password)
        elif filename != "":
            # Todo add the dir to the file in the mssautoplot.json
            dirpath = "./"
            file_path = os.path.join(dirpath, filename)
            exists = os.path.exists(file_path)
            if not exists:
                print("Filename {} doesn't exist".format(filename))
                self.pdlg.close()
                raise SystemExit("Filename {} doesn't exist".format(filename))
            self.read_ftml(filename)

    def setup(self):
        pass

    def update_path(self, filename=None):
        """
        Update the path by reading the FTML data from the given filename
         and redrawing the path based on the updated waypoints model data.

        Parameters:
        :filename: The name of the file to read FTML data from.

        Returns:
        None
        """
        # plot path and label
        if filename != "":
            self.read_ftml(filename)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        self.plotter.redraw_path(waypoints_model_data=self.wp_model_data)

    def update_path_ops(self, filename=None):
        self.setup()
        # plot path and label
        if filename != "":
            self.read_operation(filename, self.url, self.msc_auth, self.username, self.password)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        self.plotter.redraw_path(waypoints_model_data=self.wp_model_data)

    def read_ftml(self, filename):
        self.wps, self.wp_model_data = load_from_ftml(filename)
        self.wp_lats, self.wp_lons, self.wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
        self.wp_press = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in self.wps]
        self.path = [(wp[0], wp[1], datetime.now()) for wp in self.wps]
        self.vertices = [list(a) for a in (zip(self.wp_lons, self.wp_lats))]
        self.lats, self.lons = mslib.utils.coordinate.path_points([_x[0] for _x in self.path],
                                                                  [_x[1] for _x in self.path],
                                                                  numpoints=self.num_interpolation_points + 1,
                                                                  connection="greatcircle")

    def read_operation(self, op_name, msc_url, msc_auth_password, username, password):
        self.wps, self.wp_model_data = load_from_operation(op_name, msc_url=msc_url,
                                                           msc_auth_password=msc_auth_password, username=username,
                                                           password=password)
        self.wp_lats, self.wp_lons, self.wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
        self.wp_press = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in self.wps]
        self.path = [(wp[0], wp[1], datetime.now()) for wp in self.wps]
        self.vertices = [list(a) for a in (zip(self.wp_lons, self.wp_lats))]
        self.lats, self.lons = mslib.utils.coordinate.path_points([_x[0] for _x in self.path],
                                                                  [_x[1] for _x in self.path],
                                                                  numpoints=self.num_interpolation_points + 1,
                                                                  connection="greatcircle")


class TopViewPlotting(Plotting):
    def __init__(self, cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw=False):
        super(TopViewPlotting, self).__init__(cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw)
        self.pdlg = pdlg
        self.myfig = qt.TopViewPlotter()
        self.myfig.fig.canvas.draw()
        self.fig, self.ax = self.myfig.fig, self.myfig.ax
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.fig)
        self.myfig.init_map(**(self.params["basemap"]))
        self.plotter = mpath.PathH_Plotter(self.myfig.map)
        self.username = msc_username
        self.password = msc_password
        self.msc_auth = msc_auth_password
        self.url = msc_url
        self.raw = raw

    def setup(self):
        pass

    def draw(self, flight, section, vertical, filename, init_time, time, url, layer, style, elevation, no_of_plots):
        if filename != "" and filename == flight:
            self.update_path_ops(filename)
        elif filename != "":
            try:
                self.update_path(filename)
            except AttributeError as e:
                logging.debug(e)
                raise SystemExit("No FLIGHT Selected")

        width, height = self.myfig.get_plot_size_in_px()
        self.bbox = self.params['basemap']
        if not init_time:
            init_time = None

        kwargs = {"layers": [layer],
                  "styles": [style],
                  "time": time,
                  "init_time": init_time,
                  "exceptions": 'application/vnd.ogc.se_xml',
                  "level": elevation,
                  "srs": self.config["predefined_map_sections"][section]["CRS"],
                  "bbox": (self.bbox['llcrnrlon'], self.bbox['llcrnrlat'],
                           self.bbox['urcrnrlon'], self.bbox['urcrnrlat']
                          ),
                  "format": "image/png",
                  "size": (width, height)
                }

        auth_username, auth_password = get_auth_from_url_and_name(url, self.config["MSS_auth"])
        # bbox for 1.3.0 needs a fix, swapped order
        wms = MSUIWebMapService(url,
                                username=auth_username,
                                password=auth_password,
                                version='1.1.1')

        img = wms.getmap(**kwargs)
        image_io = io.BytesIO(img.read())
        img = PIL.Image.open(image_io)
        t = str(time)
        date_time = re.sub(r'\W+', '', t)
        plot_filename = slugify(f"{flight}_{layer}_{section}_{date_time}_{no_of_plots}_{elevation}") + ".png"
        if self.raw:
            img.save(plot_filename)
        else:
            self.myfig.draw_image(img)
            self.myfig.fig.savefig(plot_filename)
        print(f"The image is saved at: {os.getcwd()}/{plot_filename}")


class SideViewPlotting(Plotting):
    def __init__(self, cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw=False):
        super(SideViewPlotting, self).__init__(cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw)
        self.pdlg = pdlg
        self.myfig = qt.SideViewPlotter()
        self.ax = self.myfig.ax
        self.fig = self.myfig.fig
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.fig.canvas.draw()
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.plotter = mpath.PathV_Plotter(self.myfig.ax)
        self.username = msc_username
        self.password = msc_password
        self.msc_auth = msc_auth_password
        self.url = msc_url

    def setup(self):
        self.intermediate_indexes = []
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
            if abs(lat - self.wps[ipoint][0]) < 1E-10 and abs(lon - self.wps[ipoint][1]) < 1E-10:
                self.intermediate_indexes.append(i)
                ipoint += 1
            if ipoint >= len(self.wps):
                break
        self.myfig.setup_side_view()
        times = None
        times_visible = False
        self.myfig.redraw_xaxis(self.lats, self.lons, times, times_visible)

    def update_path(self, filename=None):
        """
        Update the path by reading the FTML data from the given filename
         and redrawing the path based on the updated waypoints model data.

        Parameters:
        :filename: The name of the file to read FTML data from.

        Returns:
        None
        """
        # plot path and label
        if filename != "":
            self.read_ftml(filename)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        indices = list(zip(self.intermediate_indexes, self.wp_press))
        self.plotter.redraw_path(vertices=indices,
                                 waypoints_model_data=self.wp_model_data)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def update_path_ops(self, filename=None):
        self.setup()
        # plot path and label
        if filename != "":
            self.read_operation(filename, self.url, self.msc_auth, self.username, self.password)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        indices = list(zip(self.intermediate_indexes, self.wp_press))
        self.plotter.redraw_path(vertices=indices,
                                 waypoints_model_data=self.wp_model_data)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def draw(self, flight, section, vertical, filename, init_time, time, url, layer, style, elevation, no_of_plots):
        if filename != "" and filename == flight:
            self.update_path_ops(filename)
        elif filename != "":
            try:
                self.update_path(filename)
            except AttributeError as e:
                logging.debug(e)
                raise SystemExit("No FLIGHT Selected")
        width, height = self.myfig.get_plot_size_in_px()
        p_bot, p_top = [float(x) * 100 for x in vertical.split(",")]
        self.bbox = tuple([x for x in (self.num_interpolation_points,
                          p_bot / 100, self.num_labels, p_top / 100)]
                         )

        if not init_time:
            init_time = None

        kwargs = {"layers": [layer],
                  "styles": [style],
                  "time": time,
                  "init_time": init_time,
                  "exceptions": 'application/vnd.ogc.se_xml',
                  "srs": "VERT:LOGP",
                  "path_str": ",".join(f"{wp[0]:.2f},{wp[1]:.2f}" for wp in self.wps),
                  "bbox": self.bbox,
                  "format": "image/png",
                  "size": (width, height)
                }

        auth_username, auth_password = get_auth_from_url_and_name(url, self.config["MSS_auth"])
        # bbox for sideview is correct
        wms = MSUIWebMapService(url,
                                username=auth_username,
                                password=auth_password,
                                version='1.3.0')

        img = wms.getmap(**kwargs)
        image_io = io.BytesIO(img.read())
        img = PIL.Image.open(image_io)
        plot_filename = slugify(f"{flight}_{layer}_{time}_{no_of_plots}") + ".png"
        self.myfig.setup_side_view()
        self.myfig.draw_image(img)
        self.ax.set_title(f"{flight}: {layer} \n{time} {no_of_plots}", horizontalalignment="left", x=0)
        self.myfig.redraw_xaxis(self.lats, self.lons, None, False)
        self.myfig.draw_image(img)
        self.myfig.fig.savefig(plot_filename, bbox_inches='tight')
        print(f"The image is saved at: {os.getcwd()}/{plot_filename}")


class LinearViewPlotting(Plotting):
    # ToDo Implement access of MSColab
    def __init__(self, cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw=False):
        super(LinearViewPlotting, self).__init__(cpath, msc_url, msc_auth_password, msc_username, msc_password, raw)
        self.pdlg = pdlg
        self.myfig = qt.LinearViewPlotter()
        self.ax = self.myfig.ax
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.plotter = mpath.PathV_Plotter(self.myfig.ax)
        self.fig = self.myfig.fig
        self.username = msc_username
        self.password = msc_password
        self.msc_auth = msc_auth_password
        self.url = msc_url

    def setup(self):

        linearview_size_settings = config_loader(dataset="linearview")
        settings_dict = {"plot_title_size": linearview_size_settings["plot_title_size"],
                         "axes_label_size": linearview_size_settings["axes_label_size"]}
        self.myfig.set_settings(settings_dict)
        self.myfig.setup_linear_view()

    def update_path(self, filename=None):
        self.setup()
        if filename != "":
            self.read_ftml(filename)

        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def update_path_ops(self, filename=None):
        self.setup()
        # plot path and la
        # plot path and label
        if filename != "":
            self.read_operation(filename, self.url, self.msc_auth, self.username, self.password)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def draw(self, flight, section, vertical, filename, init_time, time, url, layer, style, elevation, no_of_plots):
        if filename != "" and filename == flight:
            self.update_path_ops(filename)
        elif filename != "":
            try:
                self.update_path(filename)
            except AttributeError as e:
                logging.debug(e)
                raise SystemExit("No FLIGHT Selected")
        width, height = self.myfig.get_plot_size_in_px()
        self.bbox = (self.num_interpolation_points,)

        if not init_time:
            init_time = None

        auth_username, auth_password = get_auth_from_url_and_name(url, self.config["MSS_auth"])
        wms = MSUIWebMapService(url,
                                username=auth_username,
                                password=auth_password,
                                version='1.3.0')

        path_string = ""
        for i, wp in enumerate(self.wps):
            path_string += f"{wp[0]:.2f},{wp[1]:.2f},{self.wp_press[i]},"
        path_string = path_string[:-1]
        kwargs = {"layers": [layer],
                  "styles": [style],
                  "time": time,
                  "init_time": init_time,
                  "exceptions": 'application/vnd.ogc.se_xml',
                  "srs": "LINE:1",
                  "path_str": path_string,
                  "bbox": self.bbox,
                  "format": "text/xml",
                  "size": (width, height)
                  }
        xmls = wms.getmap(**kwargs)

        if not isinstance(xmls, list):
            xmls = [xmls]

        xml_objects = []
        for xml_ in xmls:
            xml_data = etree.fromstring(xml_.read())
            xml_objects.append(xml_data)

        self.myfig.draw_image(xml_objects, colors=None, scales=None)
        self.myfig.redraw_xaxis(self.lats, self.lons)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        plot_filename = slugify(f"{flight}_{layer}") + ".png"
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)
        self.myfig.ax.set_title(f"{flight}: {layer} \n{time} {no_of_plots}", horizontalalignment="left", x=0)
        self.myfig.fig.savefig(plot_filename, bbox_inches='tight')
        print(f"The image is saved at: {os.getcwd()}/{plot_filename}")


@click.command()
@click.option('--cpath', default=constants.MSS_AUTOPLOT, help='Path of the configuration file.')
@click.option('--view', default="top", help='View of the plot (top/side/linear).')
@click.option('--ftrack', default="", help='Flight track.')
@click.option('--itime', default="", help='Initial time.')
@click.option('--vtime', default="", help='Valid time.')
@click.option('--intv', default=0, help='Time interval.')
@click.option('--stime', default="", help='Starting time for downloading multiple plots with a fixed interval.')
@click.option('--etime', default="", help='Ending time for downloading multiple plots with a fixed interval.')
@click.option('--raw', default=False, help='Saves the raw image with its projection in topview')
@click.pass_context
def main(ctx, cpath, view, ftrack, itime, vtime, intv, stime, etime, raw):
    pdlg = None

    def close_process_dialog(pdlg):
        pdlg.close()

    if ctx.obj is not None:
        # ToDo find a simpler solution, on a split of the package, QT is expensive for such a progressbar
        pdlg = QProgressDialog("Downloading images", "Cancel", 0, 10, parent=ctx.obj)
        pdlg.setMinimumDuration(0)
        pdlg.repaint()
        pdlg.canceled.connect(lambda: close_process_dialog(pdlg))
        pdlg.setWindowModality(Qt.WindowModal)
        pdlg.setAutoReset(True)     # Close dialog automatically when reaching max value
        pdlg.setAutoClose(True)     # Automatically close when value reaches maximum
        pdlg.setValue(0)            # Initial progress value

        # Set window flags to ensure visibility and modality
        pdlg.setWindowFlags(pdlg.windowFlags() | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        pdlg.setValue(0)

    conf.read_config_file(path=cpath)
    config = conf.config_loader()

    # flight_name = config["automated_plotting_flights"][0][0]
    # file = config["automated_plotting_flights"][0][3]
    if ctx.obj is not None:
        pdlg.setValue(1)

    msc_url = config["mscolab_server_url"]
    msc_auth_password = mslib.utils.auth.get_password_from_keyring(service_name=f"MSCOLAB_AUTH_{msc_url}",
                                                                   username="mscolab")
    msc_username = config["MSS_auth"][msc_url]
    msc_password = mslib.utils.auth.get_password_from_keyring(service_name=msc_url, username=msc_username)

    # Choose view (top or side)
    if view == "top":
        top_view = TopViewPlotting(cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw)
        sec = "automated_plotting_hsecs"
    elif view == "side":
        side_view = SideViewPlotting(cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw)
        sec = "automated_plotting_vsecs"
    elif view == "linear":
        linear_view = LinearViewPlotting(cpath, msc_url, msc_auth_password, msc_username, msc_password, pdlg, raw)
        sec = "automated_plotting_lsecs"
    else:
        print("Invalid view")

    if ctx.obj is not None:
        pdlg.setValue(2)

    def draw(no_of_plots):
        try:
            if view == "top":
                top_view.draw(flight, section, vertical, filename, init_time, time,
                              url, layer, style, elevation, no_of_plots)
            elif view == "side":
                side_view.draw(flight, section, vertical, filename, init_time, time,
                               url, layer, style, elevation, no_of_plots=no_of_plots)
            elif view == "linear":
                linear_view.draw(flight, section, vertical, filename, init_time, time,
                                 url, layer, style, elevation, no_of_plots)
            else:
                print("View is not available, Plot not created!")
                return False
        except Exception as e:
            if "times" in str(e):
                print("Invalid times and/or levels requested")
            elif "LAYER" in str(e):
                print(f"Invalid LAYER '{layer}' requested")
            elif "404 Client Error" in str(e) or "NOT FOUND for url" in str(e):
                print("Invalid STYLE and/or URL requested")
            else:
                print(str(e))
        else:
            print("Plot downloaded!")
            return True
        return False
    if ctx.obj is not None:
        pdlg.setValue(4)
    flag = False
    for flight, section, vertical, filename, init_time, time in config["automated_plotting_flights"]:
        if ctx.obj is not None:
            pdlg.setValue(8)
        for url, layer, style, elevation in config[sec]:
            if vtime == "" and stime == "":
                no_of_plots = 1
                flag = draw(no_of_plots)
            elif intv == 0:
                if itime != "":
                    init_time = datetime.strptime(itime, "%Y-%m-%dT%H:%M:%S")
                time = datetime.strptime(vtime, "%Y-%m-%dT%H:%M:%S")
                if ftrack != "":
                    flight = ftrack
                no_of_plots = 1
                flag = draw(no_of_plots)
            elif intv > 0:
                if itime != "":
                    init_time = datetime.strptime(itime, "%Y-%m-%dT%H:%M:%S")
                starttime = datetime.strptime(stime, "%Y-%m-%dT%H:%M:%S")
                endtime = datetime.strptime(etime, "%Y-%m-%dT%H:%M:%S")
                i = 1
                time = starttime
                while time <= endtime:
                    logging.debug(time)
                    if ftrack != "":
                        flight = ftrack
                    no_of_plots = i
                    flag = draw(no_of_plots)
                    time = time + timedelta(hours=intv)
                    i += 1
            else:
                raise Exception("Invalid interval")
    if ctx.obj is not None:
        pdlg.setValue(10)
        pdlg.close()
        if flag:
            QMessageBox.information(
                ctx.obj,  # The parent widget (use `None` if no parent)
                "SUCCESS",  # Title of the message box
                "Plots downloaded successfully."  # Message text
            )
        else:
            QMessageBox.information(
                ctx.obj,  # The parent widget (use `None` if no parent)
                "FAILURE",  # Title of the message box
                "Plots couldnot be downloaded."  # Message text
            )


if __name__ == '__main__':
    main()
