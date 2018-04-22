mss - User Interface
======================================

The executable for the user interface application is "**mss**".
A short description of how to start the program is given by the --help option.
Warnings about CDAT features are due to the NAppy package and can be ignored.
The program should open the main window of the user interface, from which you can
open further windows, including top view, side view and so on.

Configuration for the user interface is located in
"mss_settings.json". In this file, you can specify, for instance, the
default WMS URLs for the WMS client, the size of the local image cache
(the MSUI caches retrieved WMS images to accelerate repeated
retrievals), or the predefined locations that the user can select in
the table view.

A few options influencing the appearance of the displayed plots and
flight tracks (colours etc.) can be set directly in the user
interface (top view and side view).

.. _mss-configuration:

Configuration of mss
++++++++++++++++++++

For storage capabilities mss uses the `pyfilesystem <http://pyfilesystem2.readthedocs.io>` approach.
The default data dir is predefined as a directory: `~/mssdata` which is the same as `osfs://~/mssdata`.


PyFilesystem can open a filesystem via an *FS URL*, which is similar to a URL you might enter in to a
browser. FS URLs are useful if you want to specify a filesystem dynamically, such as in a conf file or
from the command line.


Format
------

FS URLs are formatted in the following way::

    <protocol>://<username>:<password>@<resource>

The components are as follows:

* ``<protocol>`` Identifies the type of filesystem to create. e.g. ``osfs``, ``ftp``.
* ``<username>`` Optional username.
* ``<password>`` Optional password.
* ``<resource>`` A *resource*, which may be a domain, path, or both.

Here are a few examples::

    osfs://~/projects
    osfs://c://system32
    ftp://ftp.example.org/pub
    mem://
    ftp://[user[:password]@]host[:port]/[directory]
    webdav://[user[:password]@]host[:port]/[directory]
    ssh://[user[:password]@]host[:port]/[directory]


Settings file
.............

This file includes configuration settings central to the entire
Mission Support User Interface (mss). Among others, define

 - available map projections
 - vertical section interpolation options
 - the lists of predefined web service URLs
 - predefined waypoints for the table view

If you don't have a mss_settings.json then default configuration is in place.

Store this mss_settings.json in a path, e.g. "$HOME/.config/mss"

The file could be loaded by the File Load Configuration dialog or
by the environment variable MSS_SETTINGS pointing to your mss_settings.json.

**/$HOME/.config/mss/mss_settings.json**


.. literalinclude:: samples/config/mss/mss_settings.json.sample


Flight track import/export
~~~~~~~~~~~~~~~~~~~~~~~~~~

As the planned flight track has to be quickly communicated to different parties having different
desired file formats, MSS supports a simple plugin system for exporting planned flights and
importing changed files back in addition to the main FTML format. These filters may be accessed
from the File menu of the Main Window.

MSS currently offers several import/export filters in the mslib.plugins.io module, which may serve
as an example for the definition of own plugins. The CSV plugin is enabled by default. Enabling the
experimental FliteStar text import plugin would require those lines in the UI settings file:

.. code:: json

    "import_plugins": {
        "FliteStar": ["txt", "mslib.plugins.io.flitestar", "load_from_flitestar"]
    },

The dictionary entry defines the name of the filter in the File menu. The list specifies in this
order the extension, the python module implementing the function, and finally the function name.
The module may be placed in any location of the PYTHONPATH or into the configuration directory
path.

An exemplary test file format that can be ex- and imported may be activated by:

.. code:: json

    "import_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"]
    },
    "export_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]
    },

The given plugins demonstrate, how additional plugins may be implemented. Please be advised that several
attributes of the waypoints are automatically computed by MSS (for example all time and performance data)
and will be overwritten after reading back the file.

Web Proxy
~~~~~~~~~

If you are in an area with a very low bandwith you may consider to use a squid web proxy
and add those lines in your mss_settings pointing to the proxy server.

.. literalinclude:: samples/config/mss/snippets/proxies.sample


Trajectory Tool
~~~~~~~~~~~~~~~

For accessing trajectory data based on NASA AMES format you need the nappy python module installed and
can configure this view by

.. literalinclude:: samples/config/mss/snippets/trajectorytool.sample


Docking Widgets Configurations
..............................


Performance
~~~~~~~~~~~

MSS may also roughly estimate the fuel consumption and thus range of the aircraft
neglecting weather conditions given a proper configuration file specifying the
aircraft performance. Such a file may be loaded using the 'performance settings' button
in Table View. The aircraft performance is specified using tables given in the JSON format.
A basic configuration looks like the following file:

.. literalinclude:: samples/config/mss/performance_simple.json.sample

This example file assumes a constant speed of 400 nm/h and a constant fuel consumption of
2900 lbs/h irrespective of flight level changes. The aircraft weight and available fuel are
also given, but these may also be adjusted in the GUI after loading.

The columns of the cruise table are aircraft weight (lbs), aircraft altitude (feet),
speed (nm/h), and fuel consumption (lbs/h). MSS bilinearily interpolates in aircraft
weight and altitude and extrapolates assuming a constant behaviour outside the given data.
The climb table specifies the aircraft performance when climbing up from 0 feet altitude,
while the descent table specifies the behaviour when descending down to 0 feet altitude.
The column headers are aircraft weight (lbs), aircraft altitude (feet), time spent (minutes),
distance required (nm), and fuel consumed (lbs). To compute the required data for a flight
level change, a bilinear interpolation in the table for current aircraft weight and the
two involved altitudes is performed and the difference of the resulting value is used in
the calculation.


Satellite Track Docking Widget
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The TopView has a docking widget allowing the visualisation of satellite tracks.
A `web site <https://cloudsgate2.larc.nasa.gov/cgi-bin/predict/predict.cgi>`_ to generate the data for
such tracks is operated by NASA. The data can be downloaded as ASCII file that can be open by the docking
widget. An example file is located at
:download:`docs/samples/satellite_tracks/satellite_predictor.txt <samples/satellite_tracks/satellite_predictor.txt>`.



KML Overlay Docking Widget
~~~~~~~~~~~~~~~~~~~~~~~~~~

The TopView has a docking widget that allows the visualization of KML files on top of the map. This feature
currently does not support all features of KML, for example, external resources such as images are not supported.
Some example KML files are located at :download:`docs/samples/kml/line.kml <samples/kml/line.kml>` and
:download:`docs/samples/kml/folder.kml <samples/kml/folder.kml>`.


File picker dialogue
~~~~~~~~~~~~~~~~~~~~

MSS supports the use of a general file picker to access locations on remote machines
facilitating collaboration on campaigns. To enable this feature apply

.. code:: json

    "filepicker_default": "fs",

to your configuration file. The allowed values are "qt" for QT-based dialogues, "fs" for
fsfile_picker-based dialogues supporting remote locations, or "default" for the default
dialogues. The default is currently identical to "qt", but may change in upcoming releases.
The dialogues may also be configured more fine grained with the parameters of
'filepicker_flightrack for saving and loading flight tracks,
'filepicker_matplotlib' for saving figures, "filepicker_config" for loading json configuration
files, "filepicker_performance" for loading performance data, "filepicker_satellitetrack" for 
loading satellite track data, and "filepicker_trajectories" for loading data in the
trajectory tool. Additionally, the dialogue type may be configured for each export/import plugin
individually by a fourth, optional, parameter.

data dir
~~~~~~~~

With using the "filepicker_default": "fs" setting you can enable any implemented
`pyfilesystem2 <http://pyfilesystem2.readthedocs.io/en/latest/openers.html>`_ fs url.
Additional to the builtin fs urls we have added optional the `webdavfs <https://github.com/PyFilesystem/webdavfs>`_
and `sshfs <https://github.com/libfuse/sshfs>`_ service.


With setting the option "filepicker_default": "default" you can only access local storages.

.. code:: json

  "data_dir": "~/mssdata",



Example WMS Server
++++++++++++++++++

Some public accessible WMS Servers

 * http://osmwms.itc-halle.de/maps/osmfree
 * http://ows.terrestris.de/osm/service
 * https://firms.modaps.eosdis.nasa.gov/wms
