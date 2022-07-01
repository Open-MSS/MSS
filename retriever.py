import sys
import argparse
import datetime
import io
import os
import xml
import requests
from fs import open_fs
import PIL.Image

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
from mslib.msui import mpl_pathinteractor as mp
from mslib.msui import flighttrack as ft


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

            # plot path and labels
            fig.canvas.draw()
            waypoints = ft.WaypointsTableModel(filename=filename)
            mp.HPathInteractor(bm, waypoints)

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
            [_x[0] for _x in path], [_x[1] for _x in path], numpoints=num_interpolation_points + 1, connection="greatcircle")
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
            bbox = ",".join(str(x) for x in (num_interpolation_points, p_bot / 100, num_labels, p_top / 100))
            ax.grid(b=True)
            ax.patch.set_facecolor("None")
            pres_maj = mslib.msui.mpl_qtwidget.MplSideViewCanvas._pres_maj
            pres_min = mslib.msui.mpl_qtwidget.MplSideViewCanvas._pres_min
            major_ticks = pres_maj[(pres_maj <= p_bot) & (pres_maj >= p_top)]
            minor_ticks = pres_min[(pres_min <= p_bot) & (pres_min >= p_top)]
            labels = ["{}".format(int(l / 100.))
                      if (l / 100.) - int(l / 100.) == 0 else "{}".format(float(l / 100.)) for l in major_ticks]
            if len(labels) > 20:
                labels = ["" if x.split(".")[-1][0] in "975" else x for x in labels]
            elif len(labels) > 10:
                labels = ["" if x.split(".")[-1][0] in "9" else x for x in labels]
            ax.set_ylabel("pressure (hPa)")
            ax.set_yticks(minor_ticks, minor=True)
            ax.set_yticks(major_ticks, minor=False)
            ax.set_yticklabels([], minor=True, fontsize=10)
            ax.set_yticklabels(labels, minor=False, fontsize=10)
            ax.set_ylim(p_bot, p_top)
            ax.set_xlim(0, num_interpolation_points)
            ax.set_xticks(range(0, num_interpolation_points, tick_index_step))
            ax.set_xticklabels(
                [f"{x[0]:2.1f}, {x[1]:2.1f}"
                 for x in zip(lats[::tick_index_step], lons[::tick_index_step])],
                rotation=25, fontsize=10, horizontalalignment="right")
            ax.set_xlabel("lat/lon")

            # plot path and waypoint labels
            ax.plot(intermediate_indexes, wp_presss,
                    color="blue", marker="o", linewidth=2, markerfacecolor="red",
                    markersize=4)
            for i, (idx, press, loc) in enumerate(zip(intermediate_indexes, wp_presss, wp_locs)):
                textlabel = "{:} ".format(loc if loc else str(i))
                plt.text(idx + 1, press, textlabel, rotation=90, **TEXT_CONFIG)
            plt.tight_layout()

            # retrieve and draw WMS image
            ax_bounds = plt.gca().bbox.bounds
            width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))
            rparams = {"version": "1.1.1", "request": "GetMap", "format": "image/png",
                       "exceptions": "application/vnd.ogc.se_xml",
                       "srs": "VERT:LOGP", "layers": layer, "styles": style,
                       "dim_init_time": init_time, "time": time,
                       "width": width, "height": height,
                       "path": ",".join(f"{wp[0]:.2f},{wp[1]:.2f}" for wp in wps),
                       "bbox": bbox}
            if not init_time:
                del rparams["dim_init_time"]
            req = requests.get(
                url, auth=tuple(config["WMS_login"][url]),
                params=rparams)

            if req.headers['Content-Type'].startswith("text/"):
                print("WMS Error:")
                print(req.text)
                print(url, params)
                print(rparams)
                print("P")
                raise RuntimeError
                exit(1)
            print(url, params)
            print(rparams)
            image_io = io.BytesIO(req.content)
            try:
                img = PIL.Image.open(image_io)
            except Exception as ex:
                print(ex)
                print(req.headers)
                print(req.content)
                raise
            imgax = fig.add_axes(ax.get_position(), frameon=True,
                                 xticks=[], yticks=[], label="ax2", zorder=0)
            imgax.imshow(img, interpolation="nearest", aspect="auto", origin="upper")
            imgax.set_xlim(0, img.size[0] - 1)
            imgax.set_ylim(img.size[1] - 1, 0)

            plt.savefig(f"{flight}_{layer}.png")


if __name__ == "__main__":
    main()
