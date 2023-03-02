MSUI (Mission Support User Interface)
=====================================

The executable for the user interface application is "**msui**".
A short description of how to start the program is given by the --help option.
The program should open the main window of the user interface, from which you can
open further windows, including top view, side view and so on.

Configuration for the user interface is located in
"msui_settings.json". In this file, you can specify, for instance, the
default WMS URLs for the WMS client, the size of the local image cache
(the MSUI caches retrieved WMS images to accelerate repeated
retrievals), or the predefined locations that the user can select in
the table view.

A few options influencing the appearance of the displayed plots and
flight tracks (colours etc.) can be set directly in the user
interface (top view and side view).

.. _msui-configuration:

Configuration of MSUI
---------------------

The settings file msui_settings file includes configuration settings central to the entire
Mission Support User Interface (msui). Among others, define

 - available map projections
 - vertical section interpolation options
 - the lists of predefined web service URLs
 - predefined waypoints for the table view

If you don't have a msui_settings.json then default configuration is in place.

Store this msui_settings.json in a path, e.g. "$HOME/.config/mss"

The file could be loaded by the File Configuration dialog or
by the environment variable msui_settings pointing to your msui_settings.json.

**/$HOME/.config/msui/msui_settings.json**


.. literalinclude:: samples/config/msui/msui_settings.json.sample

File I/O
........

For storage capabilities mss uses the `PyFilesystem2 <http://pyfilesystem2.readthedocs.io>`__ approach.
The default data dir is predefined as a directory: `~/mssdata` which is the same as `osfs://~/mssdata`.


PyFilesystem can open a filesystem via an *FS URL*, which is similar to a URL you might enter in to a
browser. FS URLs are useful if you want to specify a filesystem dynamically, such as in a conf file or
from the command line.

We have internally implemented `PyFilesystem2 <http://pyfilesystem2.readthedocs.io>`__


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



File picker dialogue
~~~~~~~~~~~~~~~~~~~~

MSS supports the use of a general file picker to access locations on remote machines
facilitating collaboration on campaigns. To enable this feature apply

.. code:: text

    "filepicker_default": "fs",

to your configuration file. The allowed values are "qt" for QT-based dialogues, "fs" for
fs_file_picker-based dialogues supporting remote locations, or "default" for the default
dialogues. The default is currently identical to "qt", but may change in upcoming releases.


With using the "filepicker_default": "fs" setting you can enable any implemented
`PyFilesystem2 <http://pyfilesystem2.readthedocs.io/en/latest/openers.html>`_ fs url.
Additional to the builtin fs urls we have added optional the `webdavfs <https://github.com/PyFilesystem/webdavfs>`_
and `sshfs <https://github.com/libfuse/sshfs>`_ service.


With setting the option "filepicker_default": "default" you can only access local storages.

.. code:: text

  "data_dir": "~/mssdata",




MSUI Flight track import/export plugins
.......................................


MSS currently offers several import/export filters in the mslib.plugins.io module, which may serve
as an example for the definition of own plugins. Take care that added plugins use different file extensions.
They are listed below. The CSV plugin is enabled by default.
Enabling the experimental FliteStar text import plugin would require those lines in
the UI settings file:

.. code:: text

    "import_plugins": {
        "FliteStar": ["fls", "mslib.plugins.io.flitestar", "load_from_flitestar"]
    },


More details about Plugins on :ref:`msuiplugins`.
    
    
Web Proxy
.........

If you are in an area with a very low bandwidth you may consider to use a squid web proxy
and add those lines in your msui_settings pointing to the proxy server.

.. literalinclude:: samples/config/msui/snippets/proxies.sample


Caching
.......

For changing the default cache directory and behaviour to a named directory
you can use these parameters. If you use shared directories you may have to solve access rights.

.. literalinclude:: samples/config/msui/snippets/caching.sample


Docking Widgets Configurations
------------------------------


Performance
...........

MSS may also roughly estimate the fuel consumption and thus range of the aircraft
neglecting weather conditions given a proper configuration file specifying the
aircraft performance. Such a file may be loaded using the 'performance settings' button
in Table View. The aircraft performance is specified using tables given in the JSON format.
A basic configuration looks like the following file:

.. literalinclude:: samples/config/msui/performance_simple.json.sample

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
..............................

The TopView has a docking widget allowing the visualisation of satellite tracks.
A `web site <https://cloudsgate2.larc.nasa.gov/cgi-bin/predict/predict.cgi>`_ to generate the data for
such tracks is operated by NASA. The data can be downloaded as ASCII file that can be open by the docking
widget. An example file is located at
:download:`docs/samples/satellite_tracks/satellite_predictor.txt <samples/satellite_tracks/satellite_predictor.txt>`.



KML Overlay Docking Widget
..........................


The TopView has a docking widget that allows the visualization of KML files on top of the map.

This feature supports all *essential* elements of KML relevant to MSS' usage namely:

* Placemarks (*present in Folder/ Document or otherwise*)
* Style (LineStyle & PolyStyle)
* Geometries defined in KML such as

   - Point
   - LineString
   - LinearRing
   - Polygon (*Inner and Outer Rings*)
   - MultiGeometries (*MultiPoint, MultiLineString, MultiPolygon*)
   - Geometry Collection (*combination of various types of MultiGeometries*)


The KML Support has been enhanced to parse all legal KML Files without crashing, and a clear visualization
on the map, with the relevant geometries and styles.

The KML Interface now supports display of multiple KML Files simultaneously, with easy to use Buttons such
as 'Add KML Files', 'Remove File', 'Select/ Unselect All Files' for the user's benefit.

A Check/ Uncheck feature allows users to display/hide individual plots on the map, at the User's leisure.

A **KML Customize Option** improves the User Experience by allowing user to customize the colour & linewidth
of each of the KML Files displayed, realtime. This allows for better understanding of the map and the plots.
(*The Customize Option can be accessed for each file, by double clicking on the name of that file in the list.*)

The 'Merge KML Files' Button allows users to combine all the displayed plotted files, to be *combined* into a
single KML File 'output.kml', which will be present in the last working directory of the user.


*Have to head out somewhere? Important KML Files open?*
Close the software with ease of mind. Next time you open your software, all your work will be present, right where
you left it! KML Overlay supports **Saving Open files** so that you can jump back in, anytime!


KML Examples
~~~~~~~~~~~~

Curious to test out some KML Files? We have a vibrant sample collection ready just for this!

Example KML Files are located at :

* Displays LineString :download:`docs/samples/kml/line.kml <samples/kml/line.kml>`
* Displays Point & Polygon :download:`docs/samples/kml/folder.kml <samples/kml/folder.kml>`
* Displays Polygon :download:`docs/samples/kml/color.kml <samples/kml/color.kml>`
* Displays Style (*The green blob with the Airport*) :download:`docs/samples/kml/style.kml <samples/kml/style.kml>`
* Displays Area in South America (*Points, LineStrings, Polygons*) :download:`docs/samples/kml/features.kml <samples/kml/features.kml>`
* Displays the World Map (*MultiPolygon*) :download:`docs/samples/kml/World_Map.kml <samples/kml/World_Map.kml>`
* Displays Square Fractal plot in North America (*Polygon Rings*) :download:`docs/samples/kml/polygon_inner.kml <samples/kml/polygon_inner.kml>`
* Displays Fork like pattern in Ireland (*MultiLineStrings*) :download:`docs/samples/kml/Multilinestrings.kml <samples/kml/Multilinestrings.kml>`
* Displays Geometry Collection in Adelaide, Australia  :download:`docs/samples/kml/geometry_collection.kml <samples/kml/geometry_collection.kml>`


Remote sensing Docking Widget
.............................

The TopView has a docking widget that allows the visualization of remote sensing related features.
It may visualize the position of tangent points of limb sounders and can overlay the flight path with colours
according to the relative position of sun, moon, and some planets (to either avoid or seek out alignments).
Upon first starting the widget, it is thus necessary to download astronomic positional data
(`see here for more information <http://rhodesmill.org/skyfield/files.html>`_).
This is automatically performed by the skyfield python package, retrieving the data from public sources of JPL
and other US services. The data is stored in the MSS configuration directory and may need to update irregularly.






publicly accessible WMS Servers
-------------------------------

Some examples for publicly accessible WMS Servers

 * http://osmwms.itc-halle.de/maps/osmfree
 * http://ows.terrestris.de/osm/service
 * http://eumetview.eumetsat.int/geoserver/wms
 * https://apps.ecmwf.int/wms/?token=public
 * https://maps.dwd.de/geoserver/wms


Automation using the WMS API
============================

Besides using the MSS UI we can use the API of the WMS sercer by a script to create
for instance a number of the same plots or several flights or several forecast steps.

The retriever is an example which needs tweaked before using it

.. literalinclude:: samples/automation/retriever.py
