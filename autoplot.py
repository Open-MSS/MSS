import click
from mslib import plot
from datetime import datetime, timedelta


@click.command()
@click.option('--itime', default="", help='Initial time.')
@click.option('--vtime', multiple=True, help='Valid time.')
@click.option('--intv', default=3, help='Time interval.')
def autoplot(itime, vtime, intv):
    if(itime == ""):
        inittime = ""
        time = vtime[0]
        validtime = vtime[1]
    elif(len(vtime) == 1):
        inittime = itime
        time = itime
        validtime = vtime[0]
    time = datetime.strptime(time, "%Y-%m-%dT" "%H:%M:%S")
    validtime = datetime.strptime(validtime, "%Y-%m-%dT" "%H:%M:%S")
    i = 1
    while(time <= validtime):
        print(time)
        print(validtime)
        a = plot.TopViewPlotting(inittime, time, no_of_plots=i)
        a.TopViewPath()
        a.TopViewDraw()
        time = time + timedelta(hours=intv)
        i = i + 1


if __name__ == '__main__':
    autoplot()
