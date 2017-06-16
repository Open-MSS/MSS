mss - User Interface
======================================

The executable for the user interface application is "**mss**". It
does not provide any command line options. Warnings about CDAT
features are due to the NAppy package and can be ignored. The program
should open the main window of the user interface, from which you can
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


Settings file
.............

This file includes configuration settings central to the entire
Mission Support User Interface (mss). Among others, define

 - available map projections
 - vertical section interpolation options
 - the lists of predefined web service URLs
 - predefined waypoints for the table view
 - batch products for the loop view in this file.

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

Loop View
~~~~~~~~~

If you have an image server you can configure the loop view by

.. literalinclude:: samples/config/mss/snippets/loopview.sample

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


Example WMS Server
..................

Some public accessible WMS Servers

 * http://osmwms.itc-halle.de/maps/osmfree
 * http://ows.terrestris.de/osm/service
 * https://firms.modaps.eosdis.nasa.gov/wms
