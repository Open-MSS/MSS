import click
from mslib import plot
from datetime import datetime, timedelta
from mslib.utils import config as conf


@click.command()
@click.option('--ftrack', default="", help='Flight track.')
@click.option('--itime', default="", help='Initial time.')
@click.option('--vtime', default="", help='Valid time.')
@click.option('--intv', default=0, help='Time interval.')
@click.option('--stime', default="", help='Starting time for downloading multiple plots.')
@click.option('--etime', default="", help='Initial time for downloading multiple plots.')
def autoplot(ftrack, itime, vtime, intv, stime, etime):
    conf.read_config_file()
    config = conf.config_loader()
    a = plot.TopViewPlotting()
    for flight, section, vertical, filename, init_time, time in \
        config["automated_plotting_flights"]:
        for url, layer, style, elevation in config["automated_plotting_hsecs"]:
            if(intv == 0):
                if(itime != ""):
                    inittime = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                else:
                    inittime = itime
                time = datetime.strptime(vtime, "%Y-%m-%dT" "%H:%M:%S")
                if(ftrack != ""):
                    flight = ftrack
                a.TopViewPath()
                a.draw(flight, section, vertical, filename, init_time,
                       time, url, layer, style, elevation, no_of_plots=1)
            else:
                if(itime != ""):
                    inittime = datetime.strptime(itime, "%Y-%m-%dT" "%H:%M:%S")
                else:
                    inittime = itime
                starttime = datetime.strptime(stime, "%Y-%m-%dT" "%H:%M:%S")
                endtime = datetime.strptime(etime, "%Y-%m-%dT" "%H:%M:%S")
                i = 1
                time = starttime
                while(time <= endtime):
                    print(time)
                    print(endtime)
                    if(ftrack != ""):
                        flight = ftrack
                    a.TopViewPath()
                    a.draw(flight, section, vertical, filename, inittime,
                           time, url, layer, style, elevation, no_of_plots=i)
                    time = time + timedelta(hours=intv)
                    i = i + 1


if __name__ == '__main__':
    autoplot()
