Changelog
=========

Version 1.6.2
-------------

Bug Fixes:
 - Update MSSChemDataAccess from example configuration in documentation, #291
 - cfg pickle files of older Version cause a crash of more recent MSS under windows only, #284
 - flightstar input plugin rounds coordinates, #283
 - DefaultDataAccess class crashes in case that two files of same
   vertical coordinate type have different number of levels, #282


Version 1.6.1
-------------

Bug Fixes:
 - Location names are not displayed in Table view, #281


Version 1.6.0
-------------

New Features:
 - disable traceback for server, #156
 - hybrid sigma coordinate whould work with float values, #203
 - WMS data access classes difficult to set up, #210
 - add mss to docker platform, 211
 - loading a flighttrackfile does not set filename, #214
 - MSWMS consistency checks for data files, #218
 - Provide units field to Plot routines, #219
 - WMS Server get capabilities update if the data files changed, #221
 - Altitude scale in side view plots, #226
 - Add button to remove the WMS overlay graphic from flightplan, #234
 - Change wms control in such a way that the latest not the first init_time is chosen by default, #236
 - Change wms control in a way that the level keeps the same on a layer change, if feasible, #237
 - Already cached WMS information is not activated upon start of wms_control for default WMS server, #247
 - Try preloading WMS servers on startup, #250
 - traceback should show version info, #256
 - add version info to output files, #259
 - completly remove vt_cache, #260
 - update layer list on get_capabilities, #268

Bug Fixes:
 - WMS Server crashes if (some) files do not contain a variable associated with a dimension, #220
 - the proper Cf standard_name "omega" is "lagrangian_tendency_of_air_pressure", #225
 - WMS_control does not disable controls in all necessary circumstances, #239
 - MSS provides unhelpful error message when requesting unsupported projections from non-WMS servers, #244
 - WMSServer' object has no attribute 'hsec_layer_registry', #270
 - demodata vertical pressure levels contain wrong units, #276

Other Changes:
 - Remove loop view until a maintainer is found, #275


Hint:
~~~~~

DefaultDataAccess
+++++++++++++++++

With 1.6.0 we introduced a DefaultDataAccess Class. This requires a change in your server configuration.
This is an example from demodata.
data = {
   "ecmwf_EUR_LL015": mslib.mswms.dataaccess.DefaultDataAccess(_datapath, "EUR_LL015"),
}
This class substitutes all previous defined classes for data access.
The Constructor needs information on data path and domain ID, see documentation.
Also we replaced the name from nwpaccess to data.
The vt_cache caching was removed.

WMS Server
++++++++++
The server does not need a restart by new data. Any get capability request by the user loads the recent data.


Version 1.5.6
-------------

Bug Fixes:
 - Using non-US locale and pyqt4, moving points with mouse may not work, #255


Version 1.5.5
-------------

Bug Fixes:
 - Changing WP in TopView and SideView by mouse broken, #248


Version 1.5.4
-------------

Bug Fixes:
 - MSS crashes if one cancels the load performance data dialogue, #229
 - Crash in MSWMS vertical section plot If the two last waypoints share the same coordinate, #232
 - MSS crashes in SideView if the flightpath consists of exactly two identical points, #233
 - MSS crashes occasionally when moving a point in TopView, #238
 - txt export plugin broken, #240
 - Trying to clean WMC image cache may crash application (rights), #243
 - Inserting Waypoint in steorographic view is much too magnetic to locations, #245


Version 1.5.3
-------------

Bug Fixes:
 - incorrect time info on side view plots, #227
 - Coordinates close to Locations cannot be entered into TableView, #228


Version 1.5.2
-------------

Bug Fixes:
 - Server not giving WMS compliant error messages for invalid time/elevation data, #205
 - colour bar labels for generic plots do not show sufficient significant digits, #209
 - Open File Dialogue broken in PyQt5, #212
 - Table View not properly updated in PyQt5, #213


Version 1.5.1
-------------

Bug Fixes:
 - clicks on same position crashs waypoint insert for cyl projection, #197
 - existing picklefiles of py2 crash on py3 version (vice versa), #198


Version 1.5.0
-------------

New Features:
 - old OWSlib removed from repository and replaced by conda-forge package, #1
 - the get capabilities button becomes enabled if the WMS Url changes, #106
 - About of the mss ui got a link to the documentation, #110
 - About shows that we are a python powered project, #111
 - by configuration, sizes of topview, sideview, tableview,
   could be predefined and for topview and sideview set to immutable., #123
 - refactored strings to unicode, #126
 - refactored url strings, #150
 - performance data used for time information on vertical plots, #151
 - use a singleton for WMS capability storage, #168
 - ui files, _test folders excluded from conda build pacakages, #169
 - implemented virtualdisplay for linux, #172
 - cache for basemap coastline and country shape data added, #173
 - consistant naming of "as" imports, #175
 - loopview enable/disabled, based on given URL, #183
 - configurable external proxy to cache on low bandwidth transfered images, #188


Bug Fixes:
 - Graticule strange/broken for southern polar stereographic projection, #178
 - Flightpath / Location positioning problematic when crossing 180 degree E/W in cylindrical projection, #179
 - tests independent from local mss_settings.json, #191
 - catch invalid WMS Urls, #195


Other Changes:
 - line seperator of source files unified to LF, #92
 - refactored whole codebase for compatibility with python3, #176
 - version number of recent conda package added to documentation, #185
 - split mss_settings.json.sample into snippet parts, and further documentation #194

Hint:
~~~~~
This version has a lot of refactoring work.
We are now compatible with Python 3. We have not all dependent libraries verified
to behave similar as for Python 2. After done this we will build also a Python 3 package.



Version 1.4.1
-------------

Bug Fixes:
 - changing WMS Url needs to reset some options, #170
 - plugins, e.g. kml plugin can not be loaded via configuration (.json) file on any platform, #171
 - Changing map appearance deletes WMS image title, #174


Version 1.4.0
-------------

New Features:
 - Keyboard control for side/top views, #167
 - Pressure contours to MSSChem hsects added, #164
 - Export active flight track as .kml, #158
 - Integration of CLaMS-Ice data products, #155
 - mss gui got arguments on call, #153
 - Support QT5, #114
 - Enhanced KML support, #98
 - Integration of CAMS regional AQ forecast,  #95
 - Integrate prefetch functionality into msui client to speed up map loading, #2


Bug Fixes:
 - refactored wsgi auth handler, #141, #118
 - WMS Url is updated to redirect Url, #135
 - Better identification of configured layers without (valid) data, #101


Other Changes:
 - Our source now has a unified fileheader, #137
 - Loop view  and Time Series moved into the Tools menu, #136
 - MSS Icon missing from startmenu after conda install, #115
 - MSS Logo, #100
 - We worked extensive on py.test test coverage also refactored all
   existing inline code tests, #21

Hint:
~~~~~
On linux and window installing of mss will create an icon in your Desktop start menu.

Because authentication can happen as different user than the one driving the mss server
we have moved the password setup to mss_wms_auth.py


Version 1.3.3
-------------

Bug Fixes:
 - Inserting Waypoint outside of map in TopView crashes MSS, #149
 - Some of the additional tools don't close completly, #139


Version 1.3.2
-------------

Bug Fixes:
 - Generic Maps for CLaMS employ incorrect styles, #138
 - update of map on changes and style changes, #131
 - Weight from aircraft limited to 99999, #128
 - GUI load of different config.json fails, #127
 - Delete Waypoint via Top/Sideview does not work, #124
 - sideview axis too much details, #104


Version 1.3.1
-------------

Bug Fixes:
 - Inconsistent projections employed in default/sample data for client and server, #109
 - local caching needs to take care of wms url, #107
 - options of side view fails, #105
 - flight track saving shows on linux an extension problem, #102
 - Export Active Flight Track as CSV, #103


Version 1.3.0
-------------

New Features:
 - Suggest standard name for saving plots, #13
 - KML Overlay introduced for overplot of flight region borders, #61, #97
 - implemented demodata for standalone server and py.test, #80
 - simplified server setup, added demodata. 
 - Always provide simplified aircraft range estimates in TableView. #85
 - server data needs standard_name in data, #87
 - plugin infrastructure introduced for supporting file formats for flight track saving/loading, #69, #88

Bug Fixes:
 - Generic chemical Plots cannot be used in vertical cuts unless they are given on pressure grid, #62
 - config_loader overwrites internally config file, #82
 - WMS read does not recognize temperature in ECMWF data, #83
 - falling back to default configuration if mss_settings.json is missing, #89
 - PathInteractors not properly deleted when View is closed, #91

Other Changes:
 - channel atmo deprecated and removed from documentation
 - flightperformance refactored to a simpler approach, cs #5bef122
 - mss_wms_cl removed, #48
 - wms_login_cache refactored to a module of constants, #47
 - Reimplemented Hexagon Tools from Stefan using a docking widget for TableView. #18

HINT:
~~~~~

We are now based on the channel *conda-forge*, as some libraries were not in defaults of anaconda::

    $ conda config --add channels conda-forge



Version 1.2.4
-------------

Bug Fixes:
  - Flight performance computation broken, #75

Other Changes:
  - pyqt version 4.11.*, #74



Version 1.2.3
-------------

Bug Fixes:
 - check whether variables cmin, cmax are None, #68

Other Changes:
 - version dependencies removed from documentation



Version 1.2.2 
-------------

Bug Fixes:
 - initialize of basemap for GUI and WMS have to use same resolution, #60
 - resize of colorbar and its font for labels in the plots, #66
 - style "fixed colour scale" on vertical plots contain unit scaling, #67

New Features:
 - addition of age-of-air parameters to CLaMS plots, #65

Other Changes:
 - installation with conda-forge described#63

Version 1.2.1 
-------------

Bug Fixes:
 - server throws useful messages if mss_wms_settings.py is missing necessary variables, #58

Other Changes:
 - most version pinning removed, #59. Thanks to ocefpaf (conda-forge-member)

Version 1.2.0
-------------

New Features:
 - mss client, setup default configuration and json config file, #36, #37
 - mss client get capabilities update without new login, #29
 - wsgi and standalone server refactored and merged into one application,
   mswms is the new name of the standalone server #30
 - server configuration files simplified, #39
 - server templates got more variables defined in mss_wms_settings.py, #44, #45
 - geopy distance calculation dependency replaced by pyproj, #34
 - Simplification for adding or removing CLaMS parameters, #12

Bug Fixes:
 - execute bit only on executables, #40

Other Changes:
 - Isabell Krisch added to AUTHORS
 - skipped dependency of conda-forge, because geopy function replaced, #38
 - https://anaconda.org/atmo/mss introduced
 - moved of mslib.thirdparty.owslib to mslib.owslib and hardcoded all imports in owslib to mslib.owslib, #1
 - improved documentations


Version 1.1.0 
-------------

New Features:
 - Vertical section styles supported in standalone server, #10
 - More formats for exchanging flight paths implemented, #7
 - Reverse flight path, #11 
 - Displaying model data from CLaMS, #4
 - Visualisation of gravity wave forecasts, #14
 - Improved labels in plots, #8
   
Bug Fixes:
 - Improved debugging in standalone server, #9
 - Fix for Labels accumulate in plots upon saving, #5
 - PEP8, #19


Other Changes:
 - Namespace refactored, all modules dependend to mslib #24
 - Sphinx documentation introduced, #25, #26
 - Documentation on http://mss.rtfd.io 
 - Installation recipes based on conda  
 - First public release on June 28, 2016

