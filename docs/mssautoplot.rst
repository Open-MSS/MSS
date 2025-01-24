mssautoplot - A CLI tool for automation
=======================================

A CLI tool which enables users to download a set of plots according to the given configuration. The configuration for downloading the plots is located in "mssautoplot.json". In this file you can specify the default settings.

How to use
----------

The CLI tool has the following parameters:

+--------------+-------+----------------------------------------------------------------------+
| Parameter    | Type  |         Description                                                  |
+--------------+-------+----------------------------------------------------------------------+
| ``--cpath``  | TEXT  |   Path of the config file where the configuration is specified.      |
+--------------+-------+----------------------------------------------------------------------+
| ``--ftrack`` | TEXT  |   Flight track.                                                      |
+--------------+-------+----------------------------------------------------------------------+
| ``--itime``  | TEXT  |   Initial time.                                                      |
+--------------+-------+----------------------------------------------------------------------+
| ``--vtime``  | TEXT  |   Valid time.                                                        |
+--------------+-------+----------------------------------------------------------------------+
| ``--intv``   |INTEGER|   Time interval in hours.                                            |
+--------------+-------+----------------------------------------------------------------------+
| ``--stime``  | TEXT  |   Starting time for downloading multiple plots with a fixed interval.|
+--------------+-------+----------------------------------------------------------------------+
| ``--etime``  | TEXT  |   Ending time for downloading multiple plots with a fixed interval.  |
+--------------+-------+----------------------------------------------------------------------+
| ``--raw``    | BOOL  |   Saves the raw image with its projection in topview.                |
+--------------+-------+----------------------------------------------------------------------+


A short description of how to start the program is given by the ``--help`` option.

Examples
~~~~~~~~

Here are a few examples on how to use this tool,

1. ``mssautoplot --cpath mssautoplot.json``

The above command downloads the required number of plots with the default settings from mss_autoplot.json into the output folder.

2. ``mssautoplot --cpath mssautoplot.json --itime="" --vtime="2019-09-02T00:00:00"``

The above command will download all the plots configured in mss_autoplot.json of initial time "" and valid time "2019-09-02T00:00:00". This can be used to create a daily "standard set" of plots with/without an actual flight track, e.g., for daily morning briefings

For downloading plots of multiple flight tracks, specify the flight track and it's configuration in mss_autoplot.json. This can be used to create a "standard set" of plots for all actual flights of a campaign. See below:

"automated_plotting_flights": [
           ["flight1", "section1", "vertical1", "filename1", "init_time1", "time1"]
           ["flight2", "section2, "vertical2", "filename2", "init_time2", "time2"]]

3. ``mssautoplot --cpath mssautoplot.json --stime="2019-09-01T00:00:00" --etime="2019-09-02T00:00:00" --intv=6``

The above command will download plots of the with/without flight track from start time "2019-09-01T00:00:00" to end time "2019-09-02T00:00:00". The user would need to compulsorily specify the init_time and time in mss_autoplot.json inorder to use this functionality.


4. ``mssautoplot --cpath mssautoplot.json --raw=True``

This command stores the data of topview as PNG for overlays without axis, titles etc.
This could be used in systems like PLANET. You may want to set large values in the layout
of topview in the mssautoplot.json.


Settings file
--------------

This file includes configuration settings to generate plots in automated fashion. It includes,

 - View
 - URL of the WMS server
 - URL of mscolab server
 - List of layers to be plotted
 - Style
 - Elevation
 - List of initial time and forecast hours
 - List of flight paths
 - List of operations (from MSCOLAB)
 - Level
 - Map section
 - Resolution of the plot
 - Path of output folder


If you don't have a mss_autoplot.json then default configuration is in place.

Store this mss_autoplot.json in a path, e.g. “$HOME/.config/msui”

**/$HOME/.config/msui/mssautoplot.json**

.. literalinclude:: samples/config/msui/mssautoplot.json.sample
