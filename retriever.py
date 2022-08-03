# -*- coding: utf-8 -*-
"""

    mslib.retriever
    ~~~~~~~~~~~~~~~~~~~~

    automation within msui to create for instance a number of the same plots
    for several flights or several forecast steps

    This file is part of MSS.

    :copyright: Copyright 2020 Joern Ungermann
    :copyright: Copyright 2020-2022 by the MSS team, see AUTHORS.
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
import sys
import argparse
import datetime
import io
import os
import xml
from fs import open_fs
import PIL.Image
import hashlib

import mslib
import mslib.utils
import mslib.msui
import mslib.msui.mpl_map
import mslib.utils.qt
import mslib.utils.thermolib
from mslib.utils.config import config_loader, read_config_file
from mslib.utils.units import units
from mslib.msui import wms_control
import matplotlib.pyplot as plt
import numpy as np
from mslib.utils import thermolib
import defusedxml.ElementTree as etree


TEXT_CONFIG = {
    "bbox": dict(boxstyle="round", facecolor="white", alpha=0.5, edgecolor="none"),
    "fontweight": "bold", "zorder": 4, "fontsize": 6, "clip_on": True}


def load_from_ftml(filename):
    """Load a flight track from an XML file at <filename>.
    """
    _dirname, _name = os.path.split(filename)
    _fs = open_fs(_dirname)
    datasource = _fs.open(_name)
    try:
        doc = xml.dom.minidom.parse(datasource)
    except xml.parsers.expat.ExpatError as ex:
        raise SyntaxError(str(ex))

    ft_el = doc.getElementsByTagName("FlightTrack")[0]

    waypoints_list = []
    for wp_el in ft_el.getElementsByTagName("Waypoint"):

        location = wp_el.getAttribute("location")
        lat = float(wp_el.getAttribute("lat"))
        lon = float(wp_el.getAttribute("lon"))
        flightlevel = float(wp_el.getAttribute("flightlevel"))
        comments = wp_el.getElementsByTagName("Comments")[0]
        # If num of comments is 0(null comment), then return ''
        if len(comments.childNodes):
            comments = comments.childNodes[0].data.strip()
        else:
            comments = ''

        waypoints_list.append((lat, lon, flightlevel, location, comments))
    return waypoints_list


def main():
    parser = argparse.ArgumentParser(description="""
       This script automatically retrieves and stores a set of plots for the
       configured flights. The configuration is placed within the normal
       MSS frontend JSON file. E.g.

       "automated_plotting_flights": [
               ["ST25", "01 SADPAP (stereo)", "500,50",
                "/home/icg173/Documents/Flightplanning/SOUTHTRAC FP/ST25-joern.ftml",
                "2019-07-01T00:00:00Z", "2019-09-01T12:00:00Z"]
       ],
       "automated_plotting_hsecs": [
               ["https://forecast.fz-juelich.de/campaigns2019",
                "ecmwf.PVTropo01", "default", "4.0"],
               ["https://forecast.fz-juelich.de/campaigns2019",
                "ecmwf.ertel_potential_vorticity_pl", "ertel_potential_vorticity_bh", "200.0"]
       ],
       "automated_plotting_vsecs": [
               ["https://forecast.fz-juelich.de/campaigns2019",
                "ecmwf.VS_ertel_potential_vorticity_ml", "ertel_potential_vorticity_bh"],
               ["https://forecast.fz-juelich.de/campaigns2019",
                "ecmwf.TroposphereInversionLayer", ""]
       ]

       will plot flight "ST25" with configured map section "01 SADPAP (stereo)" and
       vertical range 500hPa to 50hPa from the given FTML file for init time
       "2019-07-01T00:00:00Z" and valid time "2019-09-01T12:00:00Z". The plots
       are defined in the hsecs (horizontal cross-sections) and vsecs (vertical
       cross-sections) entries given each the URL of the server, the layer name, the style,
       and, for hsec only, the elevation to plot (if necessary).
    """)
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("--debug", help="show debugging log messages on console", action="store_true", default=False)
    parser.add_argument("--logfile", help="Specify logfile location. Set to empty string to disable.", action="store",
                        default=os.path.join(mslib.msui.constants.MSUI_CONFIG_PATH, "mss_pyui.log"))
    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss_retriever)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", mslib.__version__)
        sys.exit()

    mslib.utils.setup_logging(args)

    read_config_file()
    config = config_loader()
    print("o", config["automated_plotting_vsecs"])
    print("OO")
    print(config["predefined_map_sections"])
    print(config["automated_plotting_flights"])

    num_interpolation_points = config["num_interpolation_points"]
    num_labels = config["num_labels"]
    tick_index_step = num_interpolation_points // num_labels

    fig = plt.figure()
    for flight, section, vertical, filename, init_time, time in \
            config["automated_plotting_flights"]:
        params = mslib.utils.coordinate.get_projection_params(
            config["predefined_map_sections"][section]["CRS"].lower())
        params["basemap"].update(config["predefined_map_sections"][section]["map"])
        wps = load_from_ftml(filename)
        wp_lats, wp_lons, wp_locs = [[x[i] for x in wps] for i in [0, 1, 3]]
        wp_presss = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in wps]
        for url, layer, style, elevation in config["automated_plotting_hsecs"]:
            fig.clear()
            ax = fig.add_subplot(111, zorder=99)
            bm = mslib.msui.mpl_map.MapCanvas(ax=ax, **(params["basemap"]))

            # plot path
            fig.canvas.draw()
            vertices = [list(a) for a in (zip(wp_lons, wp_lats))]
            x, y = bm.gcpoints_path([a[0] for a in vertices], [a[1] for a in vertices])
            x, y = bm(wp_lons, wp_lats)
            vertices = list(zip(x, y))
            line, = ax.plot(x, y, color="blue", linestyle='-', linewidth=2, zorder=100)
            line.set_data(list(zip(*vertices)))
            ax.draw_artist(line)
            wp_scatter = ax.scatter(x, y, color="red", s=20, zorder=3, animated=True, visible=True)
            ax.draw_artist(wp_scatter)

            # plot labels
            x, y = list(zip(*vertices))
            for i in range(len(wps)):
                textlabel = f"{wp_locs[i] if wp_locs[i] else str(i)}   "
                x, y = bm(wp_lons, wp_lats)
                ax.text(x[i],
                        y[i],
                        textlabel,
                        bbox=dict(boxstyle="round",
                                  facecolor="white",
                                  alpha=0.5,
                                  edgecolor="none"),
                        fontweight="bold",
                        zorder=4,
                        rotation=90,
                        animated=True,
                        clip_on=True,
                        visible=True
                        )

            # retrieve and draw WMS image
            ax_bounds = plt.gca().bbox.bounds
            width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))
            bbox = params['basemap']

            if not init_time:
                init_time = None

            wms = wms_control.MSUIWebMapService(url,
                                                username=config["WMS_login"][url][0],
                                                password=config["WMS_login"][url][1],
                                                version='1.3.0'
                                                )
            img = wms.getmap(layers=[layer],
                             styles=[style],
                             time=time,
                             init_time=init_time,
                             exceptions='application/vnd.ogc.se_xml',
                             level=elevation,
                             srs=config["predefined_map_sections"][section]["CRS"],
                             bbox=(bbox['llcrnrlon'], bbox['llcrnrlat'], bbox['urcrnrlon'], bbox['urcrnrlat']),
                             format='image/png',
                             size=(width, height)
                            )
            image_io = io.BytesIO(img.read())
            img = PIL.Image.open(image_io)

            bm.imshow(img, interpolation="nearest", origin="upper")
            bm.drawcoastlines()
            bm.drawcountries()

            fig.savefig(f"{flight}_{layer}.png")

        # prepare vsec plots
        path = [(wp[0], wp[1], datetime.datetime.now()) for wp in wps]
        lats, lons = mslib.utils.coordinate.path_points(
            [_x[0] for _x in path], [_x[1] for _x in path],
            numpoints=num_interpolation_points + 1,
            connection="greatcircle"
        )
        intermediate_indexes = []
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            if abs(lat - wps[ipoint][0]) < 1E-10 and abs(lon - wps[ipoint][1]) < 1E-10:
                intermediate_indexes.append(i)
                ipoint += 1
            if ipoint >= len(wps):
                break

        for url, layer, style in config["automated_plotting_vsecs"]:
            fig.clear()

            # setup ticks and labels
            ax = fig.add_subplot(111, zorder=99)
            ax.set_yscale("log")
            p_bot, p_top = [float(x) * 100 for x in vertical.split(",")]
            bbox = tuple([x for x in (num_interpolation_points, p_bot / 100, num_labels, p_top / 100)])
            ax.grid(b=True)
            ax.patch.set_facecolor("None")
            sideview_size_settings = config_loader(dataset="sideview")
            plot_title_size = sideview_size_settings["plot_title_size"]
            axes_label_size = sideview_size_settings["axes_label_size"]
            pres_maj = mslib.msui.mpl_qtwidget.MplSideViewCanvas._pres_maj
            pres_min = mslib.msui.mpl_qtwidget.MplSideViewCanvas._pres_min
            lat_inds = np.arange(len(lats))
            tick_index_step = len(lat_inds) // num_labels
            type = config_loader(dataset="type")

            if type == "no secondary axis":
                major_ticks = [] * units.pascal
                minor_ticks = [] * units.pascal
                labels = []
                ylabel = ""
            elif type == "pressure":
                # Compute the position of major and minor ticks. Major ticks are labelled.
                major_ticks = pres_maj[(pres_maj <= p_bot) & (pres_maj >= p_top)]
                minor_ticks = pres_min[(pres_min <= p_bot) & (pres_min >= p_top)]
                labels = [f"{int(_x / 100)}"
                        if (_x / 100) - int(_x / 100) == 0 else f"{float(_x / 100)}" for _x in major_ticks]
                if len(labels) > 20:
                    labels = ["" if x.split(".")[-1][0] in "975" else x for x in labels]
                elif len(labels) > 10:
                    labels = ["" if x.split(".")[-1][0] in "9" else x for x in labels]
                ylabel = "pressure (hPa)"
            elif type == "pressure altitude":
                bot_km = thermolib.pressure2flightlevel(p_bot * units.Pa).to(units.km).magnitude
                top_km = thermolib.pressure2flightlevel(p_top * units.Pa).to(units.km).magnitude
                ma_dist, mi_dist = 4, 1.0
                if (top_km - bot_km) <= 20:
                    ma_dist, mi_dist = 1, 0.5
                elif (top_km - bot_km) <= 40:
                    ma_dist, mi_dist = 2, 0.5
                major_heights = np.arange(0, top_km + 1, ma_dist)
                minor_heights = np.arange(0, top_km + 1, mi_dist)
                major_ticks = thermolib.flightlevel2pressure(major_heights * units.km).magnitude
                minor_ticks = thermolib.flightlevel2pressure(minor_heights * units.km).magnitude
                labels = major_heights
                ylabel = "pressure altitude (km)"
            elif type == "flight level":
                bot_km = thermolib.pressure2flightlevel(p_bot * units.Pa).to(units.km).magnitude
                top_km = thermolib.pressure2flightlevel(p_top * units.Pa).to(units.km).magnitude
                ma_dist, mi_dist = 50, 10
                if (top_km - bot_km) <= 10:
                    ma_dist, mi_dist = 20, 10
                elif (top_km - bot_km) <= 40:
                    ma_dist, mi_dist = 40, 10
                major_fl = np.arange(0, 2132, ma_dist)
                minor_fl = np.arange(0, 2132, mi_dist)
                major_ticks = thermolib.flightlevel2pressure(major_fl * units.hft).magnitude
                minor_ticks = thermolib.flightlevel2pressure(minor_fl * units.hft).magnitude
                labels = major_fl
                ylabel = "flight level (hft)"
            else:
                raise RuntimeError(f"Unsupported vertical axis type: '{type}'")

            ax.tick_params(axis='x', labelsize=axes_label_size)
            ax.set_title("vertical flight profile", fontsize=plot_title_size, horizontalalignment="left", x=0)
            ax.set_xlabel("lat/lon", fontsize=plot_title_size)
            ax.set_ylabel(ylabel, fontsize=plot_title_size)
            ax.set_yticks(minor_ticks, minor=True)
            ax.set_yticks(major_ticks, minor=False)
            ax.set_yticklabels([], minor=True)
            ax.set_yticklabels(labels, minor=False, fontsize=axes_label_size)
            ax.set_ylim(p_bot, p_top)
            ax.set_xlim(0, len(lats) - 1)
            ax.set_xticks(lat_inds[::tick_index_step])
            ax.set_xticklabels([f"{x[0]:2.1f}, {x[1]:2.1f}"
                               for x in zip(lats[::tick_index_step], lons[::tick_index_step])],
                               rotation=25, fontsize=10, horizontalalignment="right"
                               )

            # plot path
            fig.canvas.draw()
            line, = ax.plot(intermediate_indexes, wp_presss, color="blue", linestyle='-', linewidth=2, zorder=100)
            line.set_visible(True)

            # plot waypoint labels
            wp_labels = []
            for i in range(len(wps)):
                textlabel = f"{wp_locs[i] if wp_locs[i] else str(i)}"
                t = ax.text(intermediate_indexes[i],
                            wp_presss[i],
                            textlabel,
                            bbox=dict(boxstyle="round",
                                      facecolor="white",
                                      alpha=0.5,
                                      edgecolor="none"),
                            fontweight="bold",
                            zorder=4,
                            rotation=90,
                            animated=True,
                            clip_on=True,
                            visible=True
                            )
                wp_labels.append(t)
            for t in wp_labels:
                ax.draw_artist(t)

            # retrieve and draw WMS image
            ax_bounds = plt.gca().bbox.bounds
            width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))

            if not init_time:
                init_time = None

            wms = wms_control.MSUIWebMapService(url,
                                                username=config["WMS_login"][url][0],
                                                password=config["WMS_login"][url][1],
                                                version='1.3.0'
                                                )

            img = wms.getmap(layers=[layer],
                             styles=[style],
                             time=time,
                             init_time=init_time,
                             exceptions='application/vnd.ogc.se_xml',
                             srs="VERT:LOGP",
                             path_str=",".join(f"{wp[0]:.2f},{wp[1]:.2f}" for wp in wps),
                             bbox=bbox,
                             format='image/png',
                             size=(width, height)
                            )

            image_io = io.BytesIO(img.read())
            img = PIL.Image.open(image_io)
            imgax = fig.add_axes(ax.get_position(), frameon=True,
                                 xticks=[], yticks=[], label="ax2", zorder=0)
            imgax.imshow(img, interpolation="nearest", aspect="auto", origin="upper")
            imgax.set_xlim(0, img.size[0] - 1)
            imgax.set_ylim(img.size[1] - 1, 0)

            plt.savefig(f"{flight}_{layer}.xml")

        for url, layer, style in config["automated_plotting_lsecs"]:
            fig.clear()
            linearview_size_settings = config_loader(dataset="linearview")
            plot_title_size = linearview_size_settings["plot_title_size"]
            axes_label_size = linearview_size_settings["axes_label_size"]

            bbox = (num_interpolation_points,)
            lat_inds = np.arange(len(lats))
            tick_index_step = len(lat_inds) // num_labels
            ax = fig.add_subplot(111, zorder=99)

            fig.canvas.draw()
            ax.tick_params(axis='both', labelsize=axes_label_size)
            ax.set_title("Linear flight profile", fontsize=plot_title_size, horizontalalignment='left', x=0)
            ax.set_xlim(0, len(lats) - 1)
            # Set xticks so that they display lat/lon. Plot "numlabels" labels.

            ax.set_xticks(lat_inds[::tick_index_step])
            ax.set_xticklabels([f'{d[0]:2.1f}, {d[1]:2.1f}'
                                for d in zip(lats[::tick_index_step],
                                lons[::tick_index_step])],
                                rotation=25, horizontalalignment="right"
                               )
            par = ax.twinx()
            ax.set_yscale("linear")
            fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)
            ax_bounds = plt.gca().bbox.bounds
            width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))

            if not init_time:
                init_time = None

            wms = wms_control.MSUIWebMapService(url,
                                                username=config["WMS_login"][url][0],
                                                password=config["WMS_login"][url][1],
                                                version='1.3.0'
                                                )
            kwargs = {"layers": [layer],
                      "styles": [style],
                      "srs": "LINE:1",
                      "bbox": bbox,
                      "exceptions": 'application/vnd.ogc.se_xml',
                      "path_str":",".join(f"{wp_presss},{wp[0]:.2f},{wp[1]:.2f}" for wp in wps),
                      "time": time,
                      "init_time": init_time,
                      "size": (width, height),
                      "format": "text/xml"}

            xmls = wms.getmap(**kwargs)

            wms_cache = config_loader(dataset="wms_cache")
            urlstr = wms.getmap(return_only_url=True, **kwargs)
            ending = ".xml"
            md5_filename = os.path.join(wms_cache, hashlib.md5(urlstr.encode('utf-8')).hexdigest() + ending)

            with open(md5_filename, "w") as cache:
                cache.write(str(xmls.read(), encoding="utf8"))
                xmli = etree.fromstring(xmls.read())

            for i, xm in enumerate(xmli):
                data = xm.find("Data")
                values = [float(value) for value in data.text.split(",")]
                unit = data.attrib["unit"]
                numpoints = int(data.attrib["num_waypoints"])

                color = "#00AAFF"
                scale = "linear"
                offset = 40

                par = ax.twinx() if i > 0 else ax
                par.set_yscale(scale)

                par.plot(range(numpoints), values, color)
                if i > 0:
                    par.spines["right"].set_position(("outward", (i - 1) * offset))
                if unit:
                    par.set_ylabel(unit)

                fig.tight_layout()
                fig.subplots_adjust(top=0.85, bottom=0.20)
                fig.canvas.draw()

                plt.savefig(f"{flight}_{layer}.png")


if __name__ == "__main__":
    main()
