Changelog
=========


Version 1.4.0 (not released yet)
--------------------------------

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
 - Loop view  and Time Series moved into the Tools menue, #136
 - MSS Icon missing from startmenu after conda install, #115  
 - MSS Logo, #100
 - We worked extensive on py.test test coverage also refactored all
   exising tests, #21

Hint:
~~~~~~
On linux and window installing of mss will create an icon in your Desktop start menue.


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

