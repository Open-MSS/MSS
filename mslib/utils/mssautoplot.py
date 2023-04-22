"""

    mslib.utils.mssautoplot
    ~~~~~~~~~~~~~~~~~~~~~~~

    A CLI tool to create for instance a number of the same plots
    for several flights or several forecast steps

    This file is part of MSS.

    :copyright: Copyright 2022 Sreelakshmi Jayarajan
    :copyright: Copyright 2022 by the MSS team, see AUTHORS.
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

from datetime import datetime, timedelta
import io
import logging
import os
import sys

import click
import defusedxml.ElementTree as etree
import PIL.Image
import matplotlib
from fs import open_fs

import mslib
import mslib.utils
import mslib.msui
import mslib.msui.mpl_map
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
from mslib.utils.auth import get_auth_from_url_and_name


TEXT_CONFIG = {
    "bbox": dict(boxstyle="round", facecolor="white", alpha=0.5, edgecolor="none"), "fontweight": "bold",
    "zorder": 4, "fontsize": 6, "clip_on": True}


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


class Plotting:
    def __init__(self, cpath):
        read_config_file(cpath)
        self.config = config_loader()
        self.num_interpolation_points = self.config["num_interpolation_points"]
        self.num_labels = self.config["num_labels"]
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.bbox = None
        section = self.config["automated_plotting_flights"][0][1]
        filename = self.config["automated_plotting_flights"][0][3]
        try:
            self.params = mslib.utils.coordinate.get_projection_params(
                self.config["predefined_map_sections"][section]["CRS"].lower())
        except KeyError as e:
            print(e)
            sys.exit("Invalid SECTION and/or CRS")
        self.params["basemap"].update(self.config["predefined_map_sections"][section]["map"])
        self.bbox_units = self.params["bbox"]
        self.read_ftml(filename)

    def read_ftml(self, filename):
        dirpath = "./"
        file_path = os.path.join(dirpath, filename)
        exists = os.path.exists(file_path)
        if not exists:
            print("Filename {} doesn't exist".format(filename))
            sys.exit()
        self.wps, self.wp_model_data = load_from_ftml(filename)
        self.wp_lats, self.wp_lons, self.wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
        self.wp_press = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in self.wps]
        self.path = [(wp[0], wp[1], datetime.now()) for wp in self.wps]
        self.vertices = [list(a) for a in (zip(self.wp_lons, self.wp_lats))]
        self.lats, self.lons = mslib.utils.coordinate.path_points([_x[0] for _x in self.path],
                                                                  [_x[1] for _x in self.path],
                                                                  numpoints=self.num_interpolation_points + 1,
                                                                  connection="greatcircle")


class TopViewPlotting(Plotting):
    def __init__(self, cpath):
        super(TopViewPlotting, self).__init__(cpath)
        self.myfig = qt.TopViewPlotter()
        self.myfig.fig.canvas.draw()
        self.fig, self.ax = self.myfig.fig, self.myfig.ax
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.fig)
        self.myfig.init_map(**(self.params["basemap"]))
        self.plotter = mpath.PathH_Plotter(self.myfig.map)

    def update_path(self, filename=None):
        # plot path and label
        if filename is not None:
            self.read_ftml(filename)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        self.plotter.redraw_path(waypoints_model_data=self.wp_model_data)

    def draw(self, flight, section, vertical, filename, init_time, time, url, layer, style, elevation, no_of_plots):
        self.update_path(filename)

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
        wms = MSUIWebMapService(url,
                                username=auth_username,
                                password=auth_password,
                                version='1.3.0')

        img = wms.getmap(**kwargs)
        image_io = io.BytesIO(img.read())
        img = PIL.Image.open(image_io)
        self.myfig.draw_image(img)
        self.myfig.fig.savefig(f"{flight}_{layer}_{no_of_plots}.png")


class SideViewPlotting(Plotting):
    def __init__(self, cpath):
        super(SideViewPlotting, self).__init__(cpath)
        self.myfig = qt.SideViewPlotter()
        self.ax = self.myfig.ax
        self.fig = self.myfig.fig
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.fig.canvas.draw()
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.plotter = mpath.PathV_Plotter(self.myfig.ax)

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
        self.setup()
        if filename is not None:
            self.read_ftml(filename)
        self.fig.canvas.draw()
        self.plotter.update_from_waypoints(self.wp_model_data)
        indices = list(zip(self.intermediate_indexes, self.wp_press))
        self.plotter.redraw_path(vertices=indices,
                                 waypoints_model_data=self.wp_model_data)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def draw(self, flight, section, vertical, filename, init_time, time, url, layer, style, elevation, no_of_plots):
        self.update_path(filename)
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
        wms = MSUIWebMapService(url,
                                username=auth_username,
                                password=auth_password,
                                version='1.3.0')

        img = wms.getmap(**kwargs)

        image_io = io.BytesIO(img.read())
        img = PIL.Image.open(image_io)
        self.myfig.draw_image(img)
        self.myfig.fig.savefig(f"{flight}_{layer}_{no_of_plots}.png", bbox_inches='tight')


class LinearViewPlotting(Plotting):
    def __init__(self):
        super(LinearViewPlotting, self).__init__()
        self.myfig = qt.LinearViewPlotter()
        self.ax = self.myfig.ax
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.fig = self.myfig.fig

    def setup(self):
        self.bbox = (self.num_interpolation_points,)
        linearview_size_settings = config_loader(dataset="linearview")
        settings_dict = {"plot_title_size": linearview_size_settings["plot_title_size"],
                         "axes_label_size": linearview_size_settings["axes_label_size"]}
        self.myfig.set_settings(settings_dict)
        self.myfig.setup_linear_view()

    def draw(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style in self.config["automated_plotting_lsecs"]:
                width, height = self.myfig.get_plot_size_in_px()

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

                # retrieve and draw image
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

                if not type(xmls) == 'list':
                    xmls = [xmls]

                xml_objects = []
                for xml_ in xmls:
                    xml_data = etree.fromstring(xml_.read())
                    xml_objects.append(xml_data)

                self.myfig.draw_image(xml_objects, colors=None, scales=None)
                self.myfig.redraw_xaxis(self.lats, self.lons)
                highlight = [[wp[0], wp[1]] for wp in self.wps]
                self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)
                self.myfig.fig.savefig(f"{flight}_{layer}.png", bbox_inches='tight')


@click.command()
@click.option('--cpath', default=constants.MSS_AUTOPLOT, help='Path of the configuration file.')
@click.option('--view', default="top", help='View of the plot (top/side/linear).')
@click.option('--ftrack', default="", help='Flight track.')
@click.option('--itime', default="", help='Initial time.')
@click.option('--vtime', default="", help='Valid time.')
@click.option('--intv', default=0, help='Time interval.')
@click.option('--stime', default="", help='Starting time for downloading multiple plots with a fixed interval.')
@click.option('--etime', default="", help='Ending time for downloading multiple plots with a fixed interval.')
def main(cpath, view, ftrack, itime, vtime, intv, stime, etime):
    conf.read_config_file(path=cpath)
    config = conf.config_loader()
    if view == "top":
        top_view = TopViewPlotting(cpath)
        sec = "automated_plotting_hsecs"
    else:
        side_view = SideViewPlotting(cpath)
        sec = "automated_plotting_vsecs"

    def draw(no_of_plots):
        try:
            if view == "top":
                top_view.draw(flight, section, vertical, filename, init_time,
                              time, url, layer, style, elevation, no_of_plots=no_of_plots)
            elif view == "side":
                side_view.draw(flight, section, vertical, filename, init_time,
                               time, url, layer, style, elevation, no_of_plots=no_of_plots)
        except Exception as e:
            if "times" in str(e):
                print("Invalid times and/or levels requested")
            elif "LAYER" in str(e):
                print("Invalid LAYER '{}' requested".format(layer))
            elif "404 Client Error" or "NOT FOUND for url" in e:
                print("Invalid STYLE and/or URL requested")
            else:
                print(str(e))
        else:
            print("Plot downloaded!")

    for flight, section, vertical, filename, init_time, time in \
        config["automated_plotting_flights"]:
        for url, layer, style, elevation in config[sec]:
            if vtime == "" and stime == "":
                no_of_plots = 1
                draw(no_of_plots)
            elif intv == 0:
                if itime != "":
                    init_time = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                time = datetime.strptime(vtime, "%Y-%m-%dT" "%H:%M:%S")
                if ftrack != "":
                    flight = ftrack
                no_of_plots = 1
                draw(no_of_plots)
            elif intv > 0:
                if itime != "":
                    init_time = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                starttime = datetime.strptime(stime, "%Y-%m-%dT" "%H:%M:%S")
                endtime = datetime.strptime(etime, "%Y-%m-%dT" "%H:%M:%S")
                i = 1
                time = starttime
                while time <= endtime:
                    logging.debug(time)
                    if ftrack != "":
                        flight = ftrack
                    no_of_plots = i
                    draw(no_of_plots)
                    time = time + timedelta(hours=intv)
                    i = i + 1
            else:
                raise Exception("Invalid interval")


if __name__ == '__main__':
    main()
