NAVAID Plugin for exporting and importing flight path data
..........................................................

.. _navaid:

The communication of the flight path data (e.g. with the aircraft
authorities) is always individual. For this reason, import and of
these data can be done using different pre-defined templates.
Alternative plugins could be placed into the settings directory.

Details
~~~~~~~
It may be required to compute the waypoints in the format WPT012034,
where WPT is the NAVAID ID, 012 is the heading and 034 is the distance
in nautical miles. This standard is used by several flight authorities.
Data for the location of the NAVAID waypoints can be obtained as csv from
https://adds-faa.opendata.arcgis.com/search?collection=Dataset
The dataset should be named NAVAID_System.csv and placed into the subdir
plugins of the config dir.
For a given set of waypoints, the navaid export plugin exports an ASCII
table containing a column of the so-determined waypoint names. For locations
outside the given set of NAVAID points , e.g. over the oceans, the naming
convention switches to coordinate based name like xxyyNwwwzzW for
latitude xx°yy'N and longitude www°zz'W. This is done if the closest NAVAID
waypoint is more than 500 nm.

Installation
~~~~~~~~~~~~

1. Copy :download:`navaid.py </samples/plugins/navaid.py>` to a PYTHONPATH directory e.g. .config/mss

1. Save the NAVAID waypoint from https://adds-faa.opendata.arcgis.com/search?collection=Dataset select "Pending NAVAID System" and Download as CSV to your local directory `.config/mss/plugins/NAVAID_System.csv`


1. Add additional modules

   for a global installed MSS::

      pixi global add geomag geopy geographiclib



   when you have installed MSS in a Project::

       cd MSS
       pixi shell
       pixi add geomag geopy geographiclib
