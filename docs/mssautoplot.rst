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
| ``--view``   | TEXT  |   View of the plots: top (default), side or linear.                  |
+--------------+-------+----------------------------------------------------------------------+
| ``--ftrack`` | TEXT  |   Flight track.                                                      |
+--------------+-------+----------------------------------------------------------------------+
| ``--fpath``  | TEXT  |   Directory of the flight track files. Replaces the directory        |
|              |       |   stored with the file name in the config file;                      |
|              |       |   only the base name of the entry is kept.                           |
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

The above command downloads the top view plots configured in mssautoplot.json into the current working directory.
With ``--view side`` or ``--view linear`` it downloads the side or linear view plots.

2. ``mssautoplot --cpath mssautoplot.json --itime="" --vtime="2019-09-02T00:00:00"``

The above command will download all the plots configured in mssautoplot.json of initial time "" and valid time "2019-09-02T00:00:00". This can be used to create a daily "standard set" of plots with/without an actual flight track, e.g., for daily morning briefings

For downloading plots of multiple flight tracks, specify the flight track and it's configuration in mssautoplot.json. This can be used to create a "standard set" of plots for all actual flights of a campaign. See below::

    "automated_plotting_flights": [
               ["flight1", "section1", "vertical1", "filename1", "init_time1", "time1"],
               ["flight2", "section2", "vertical2", "filename2", "init_time2", "time2"]]

The section is one of the "predefined_map_sections". If the filename equals the flight name, the flight track is
the one of the MSColab operation of this name on "mscolab_server_url".

The filename is stored together with its path, e.g. "/home/mss/flights/flight1.ftml"
or "~/flights/flight1.ftml". Only then the flight track is found independent of the
directory mssautoplot is called in. A bare file name without a path is looked up in
the current working directory.

3. ``mssautoplot --cpath mssautoplot.json --stime="2019-09-01T00:00:00" --etime="2019-09-02T00:00:00" --intv=6``

The above command will download plots of the with/without flight track from start time "2019-09-01T00:00:00" to end time "2019-09-02T00:00:00". The user would need to compulsorily specify the init_time and time in mssautoplot.json in order to use this functionality.


4. ``mssautoplot --cpath mssautoplot.json --raw=True``

This command stores the data of topview as PNG for overlays without axis, titles etc.
This could be used in systems like PLANET. You may want to set large values in the layout
of topview in the mssautoplot.json.

5. ``mssautoplot --cpath mssautoplot.json --fpath /home/mss/flights/campaign2``

This command reads the flight tracks from the given directory instead of the directory
stored in mssautoplot.json. Only the base name of each stored flight track is kept,
any subdirectory stored with it is discarded, so the "/home/mss/campaign1/example.ftml"
of the configuration is loaded from "/home/mss/flights/campaign2/example.ftml".
This lets the same configuration be used for the flight tracks of several campaigns,
provided they share the file names.

On Windows give the directory in full, e.g. ``--fpath C:\Users\mss\flights\campaign2``,
recent Windows shells do not expand "~" reliably.


Settings file
--------------

This file includes configuration settings to generate plots in automated fashion. It has the format of the
msui settings file, with these entries:

 - "automated_plotting_flights": flight name, map section, vertical level, flight track file or MSColab operation,
   initial time and valid time of each set of plots
 - "automated_plotting_hsecs", "automated_plotting_vsecs", "automated_plotting_lsecs": URL of the WMS server,
   layer, style and level of the plots of the top, side and linear view
 - "predefined_map_sections": the map sections of the top view
 - "layout": the size of the plots
 - "num_interpolation_points", "num_labels": the resolution and the labels of side and linear view
 - "mscolab_server_url": the MSColab server of the operations
 - "MSS_auth": the user names of the servers; the passwords come from the keyring

All other settings have their default values. mssautoplot needs this file, it doesn't start without it.

Store this mssautoplot.json in a path, e.g. “$HOME/.config/msui”

**/$HOME/.config/msui/mssautoplot.json**

.. literalinclude:: samples/config/msui/mssautoplot.json.sample
