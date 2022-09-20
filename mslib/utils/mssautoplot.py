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
import click
import logging
from mslib import plot
from datetime import datetime, timedelta
from mslib.utils import config as conf
from mslib.msui import constants


@click.command()
@click.option('--cpath', default=constants.MSS_AUTOPLOT, help='Path of the configuration file.')
@click.option('--ftrack', default="", help='Flight track.')
@click.option('--itime', default="", help='Initial time.')
@click.option('--vtime', default="", help='Valid time.')
@click.option('--intv', default=0, help='Time interval.')
@click.option('--stime', default="", help='Starting time for downloading multiple plots with a fixed interval.')
@click.option('--etime', default="", help='Ending time for downloading multiple plots with a fixed interval.')
def main(cpath, ftrack, itime, vtime, intv, stime, etime):
    conf.read_config_file(path=cpath)
    config = conf.config_loader()
    a = plot.TopViewPlotting(cpath)
    for flight, section, vertical, filename, init_time, time in \
        config["automated_plotting_flights"]:
        for url, layer, style, elevation in config["automated_plotting_hsecs"]:
            if vtime == "" and stime == "":
                a.TopViewPath()
                a.draw(flight, section, vertical, filename, init_time,
                       time, url, layer, style, elevation, no_of_plots=1)
                click.echo("Plot downloaded!\n")
            elif intv == 0:
                if itime != "":
                    inittime = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                else:
                    inittime = itime
                time = datetime.strptime(vtime, "%Y-%m-%dT" "%H:%M:%S")
                if ftrack != "":
                    flight = ftrack
                a.TopViewPath()
                a.draw(flight, section, vertical, filename, init_time,
                       time, url, layer, style, elevation, no_of_plots=1)
                click.echo("Plot downloaded!\n")
            elif intv > 0:
                if itime != "":
                    inittime = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                else:
                    inittime = itime
                starttime = datetime.strptime(stime, "%Y-%m-%dT" "%H:%M:%S")
                endtime = datetime.strptime(etime, "%Y-%m-%dT" "%H:%M:%S")
                i = 1
                time = starttime
                while time <= endtime:
                    logging.debug(time)
                    if ftrack != "":
                        flight = ftrack
                    a.TopViewPath()
                    a.draw(flight, section, vertical, filename, inittime,
                           time, url, layer, style, elevation, no_of_plots=i)
                    time = time + timedelta(hours=intv)
                    i = i + 1
                click.echo("Plots downloaded!\n")
            else:
                raise Exception("Invalid interval")


if __name__ == '__main__':
    main()
