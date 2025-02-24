MSWMS/WMS - A OGC Web Map Server
================================

The module implements a WSGI Flask based Web Map Service 1.1.1/1.3.0 interface
to provide forecast data

from numerical weather predictions to the Mission Support User Interface.
Supported operations are GetCapabilities and GetMap for (WMS 1.1.1/1.3.0 compliant)
maps and (non-compliant) vertical sections.

  #. Configure the WMS server by modifying the settings in mswms_settings.py
     (address, products that shall be offered, ...).

  #. If you want to define new visualisation styles, the files to put them
     are mpl_hsec_styles.py and mpl_vsec_styles for maps and vertical sections,
     respectively.

For more information on WMS, see http://www.opengeospatial.org/standards/wms



.. _meteo_data:

.. _demodata:

Simulated Data and its configuration
------------------------------------


We provide demodata by executing the :code:`mswms_demodata --seed` program. This creates in your home directory
data files and also the needed server configuration files. The program creates 70MB of examples.
This script does not overwrite an existing mswms_settings.py.

::

  mss
  ├── mswms_auth.py
  ├── mswms_settings.py
  └── testdata
      ├── 20121017_12_ecmwf_forecast.ALTITUDE_LEVELS.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.CC.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.CIWC.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.CLWC.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.EMAC.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.P_derived.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.PRESSURE_LEVELS.EUR_LL015.036.pl.nc
      ├── 20121017_12_ecmwf_forecast.ProbWCB_LAGRANTO_derived.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.ProbWCB_LAGRANTO_derived.EUR_LL015.036.sfc.nc
      ├── 20121017_12_ecmwf_forecast.PV_derived.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.PVU.EUR_LL015.036.pv.nc
      ├── 20121017_12_ecmwf_forecast.Q.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.SEA.EUR_LL015.036.sfc.nc
      ├── 20121017_12_ecmwf_forecast.SFC.EUR_LL015.036.sfc.nc
      ├── 20121017_12_ecmwf_forecast.T.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.THETA_LEVELS.EUR_LL015.036.tl.nc
      ├── 20121017_12_ecmwf_forecast.U.EUR_LL015.036.ml.nc
      ├── 20121017_12_ecmwf_forecast.V.EUR_LL015.036.ml.nc
      └── 20121017_12_ecmwf_forecast.W.EUR_LL015.036.ml.nc



Before starting the standalone server you should add the path where the server config is to your python path.
e.g.

::

    $ export PYTHONPATH=~/mss



Detailed server configuration *mswms_settings.py* for this demodata

 .. literalinclude:: samples/config/mswms/mswms_settings.py.demodata

For setting authentication see *mswms_auth.py*

 .. literalinclude:: samples/config/mswms/mswms_auth.py.sample



Configuration file of the wms server
....................................

Configuration for the Mission Support System Web Map Service (wms).

In this module the data organisation structure of the available forecast
data is described. The class NWPDataAccess is subclassed for each data type
in the system and provides methods to determine which file needs to be accessed for a given variable and time.
The classes also provide methods to query the available initialisation times for a given variable,
and the available valid times for a variable and a given initialisation time. As the latter methods need
to open the NetCDF data files to determine the contained time values, a caching system is used to avoid
re-opening already searched files.

Replace the name INSTANCE in the following examples by your service name.

The configuration file have to become added to the /home/mss/INSTANCE/config directory

**/home/mss/config/mswms_settings.py**

 .. literalinclude:: samples/config/mswms/mswms_settings.py.sample


You have to adopt this file to your data.


Adopt the mswms_settings.py for your needs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you want to plot only one variable without any additional data available:

For horizontal plots:

::

  mpl_hsec_styles.make_generic_class("HS_MyStyle_pl_air_temperature",'air_temperature','pl',[],[])
  register_horizontal_layers = [
    (mpl_hsec_styles.HS_MyStyle_pl_air_temperature, ["model"]),
    ]

For vertical plots:

::

  mpl_vsec_styles.make_generic_class("VS_MyStyle_pl_air_temperature",'air_temperature','pl',[],[])
  register_vertical_layers = [
    (mpl_vsec_styles.VS_MyStyle_pl_air_temperature, ["model"]),
    ]

For linear plots:

::

  register_linear_layers = [
    (mpl_lsec_styles.LS_DefaultStyle, "air_temperature","pl", ["model"]),
    ]



Standalone server setup
-----------------------

MSWMS
.....

This module can be used to run the wms server for development using Werkzeug's development WSGI server.
The development server is not intended for use in production. For production use a production-ready WSGI server
such as Waitress, Gunicorn, Nginx, Apache2.
See also https://flask.palletsprojects.com/en/latest/tutorial/deploy/?highlight=deploy#run-with-a-production-server

.. _mswms-deployment:


For the standalone server *mswms* you need the path of your mswms_settings.py and other configuration files
added to the PYTHONPATH. E.g.::

 export PYTHONPATH=/home/mss/INSTANCE/config


For testing your server you can use the :ref:`demodata <demodata>`

The plots contained in MSS are mainly defined for meteorological forecast data. The intent is for the
user to define their own plotting classes based on the the MSS infrastructure for data access.
Some less tested plots are given as examples in the *samples* part of the documentation as templates.
The next configuration exemplarily shows how to include user defined plots:

 .. literalinclude:: samples/config/mswms/mss_chem_plots.py

 .. literalinclude:: samples/config/mswms/mswms_settings.py.chem_plots


Gallery extension
~~~~~~~~~~~~~~~~~

The gallery builder enables to generate static plots given from data and
visualisation styles on server site.
An example can be seen on the documentation based on our demodata https://mss.readthedocs.io/en/stable/gallery/index.html

When you use this feature you get a menu entry below the "Mission Support System" Main menu
on your server site.

To create all layers of all plots use
::

  mswms gallery --create

With an option `--levels` you can specify by a comma-separated list of all levels visible
on the gallery. Further options are `--itimes`, `--vtimes`.
If you want to publish on which code the images are based on you can do this by the option
`--show-code` e.g.

::

  mswms gallery --create --show-code --itimes 2012-10-17T12:00:00 --vtimes 2012-10-19T12:00:00 --levels 200,300

For the case you use an url-prefix on your site you have to add this by the `--url-prefix` parameter too.



WMS Server Deployment
---------------------

.. _deployment:

Once installation and configuration are complete, you can start the Web Map
Service application (provided you have forecast data to visualise). The file
"mswms" is an executable Python script starting up a Flask HTTP server with the
WMS WSGI module. A short description of how to start the program is given by the
--help option. The file "wms.wsgi" is intended to be used with an Apache web
server installation.

We have a single method to use data for ECMWF, CLaMS, GWFC, EMAC, METEOSAT
implemented. The data have to use for their parameters the CF attribute
standard_name. A new method should be able to deal with any CF conforming file
following a couple of simple additional requirements.

Per configuration you could register horizontal (*register_horizontal_layers*)
or vertical layers (*register_vertical_layers*), give a basemap table for EPSG
mapping (*epsg_to_mpl_basemap_table*) and at all how to access the data.

A few notes:

  - The Flask WMS currently cannot run multithreaded (Apache does
    support multiple processes). This is due to that a single instance
    of the WSGI application handler class MSS_WMSResponse can create
    only one plot at a time (otherwise you get messed up plots when
    simultaneous requests occur). In the current implementation, only a
    single instance is passed to Flask (to do all the initialisation
    work only once). To extend the software to handle simultaneous
    requests would probably involve creating a "factory" of
    MSS_WMSResponse instances.. If you want to do this, check if/how
    Flask handles "worker" factories.

  - Creating the capabilities document can take very long (> 1 min) if
    the forecast data files have to be read for the first time (the WMS
    program opens all files and tries to determine the available data
    and elevation ranges). A GetCapabilities request
    should return a document within a few seconds as long as all files
    are in the disk cache. The "CachedDataAccess" class offers an
    in-memory cache to prevent costly file-accesses beyond the first.

  - A typical bottleneck for plot generation is when the forecast data
    files are located on a different computer than the WMS server. In
    this case, large amounts of data have to be transferred over the
    network. Hence, when possible, try to make sure the WMS runs on the
    same computer on which the input data files are hosted.



Meteorological data
...................

Data for the MSS server shall be provided in CF-compliant NetCDF format. Several
specific data access methods are provided for ECMWF, Meteoc, and several other
formats.

The preferred method "DefaultDataAccess" shall supplant most of these, but
requires the data to be organised in the fashion described in the following (the
others pose mostly the same requirements).

All data files belonging to one "set" shall have a common string in its name
that can be used to uniquely identify all files of this set. Each set must share
the same time, longitude, and latitude grid. Each set must use the same
elevation layers for each type of vertical axis. Different data sets may be used
to offer different geographical regions or results of different simulation
models.

Each file of a set must contain only one or no vertical axis. If the data is
required to be given on multiple vertical axis (such as providing data for
horizontal plots on both pressure and theta levels), one (or more separate) file
for each vertical axis type must be provided. All files for one axis type shall
provide the same levels. If no vertical axis can be identified, it is assumed
that the file contains 3-D data (time, lat, lon) such as, e.g., surface pressure
or tropopause altitude.

The vertical coordinate variable is identified by the standard_name being one of
the following names:

- atmosphere_hybrid_sigma_pressure_coordinate - "ml"

- atmosphere_pressure_coordinate - "pl"

- atmosphere_ertel_potential_vorticity_coordinate - "pv"

- atmosphere_altitude_coordinate - "al"

- atmosphere_potential_temperature_coordinate - "tl"

- flight_level_coordinate -"fl"

The two-letter abbreviation is used for brief identification in the plotting
routines in addition to the standard_name of the variable to uniquely identify
which data shall be used. The data shall be organized with the dimensions in the
order of "time", "vertical coordinate", "latitudes", and "longitudes" (This is
important to reduce disk access when generating the plots). Data variables are
identified by their standard_name, which is expected to be CF compliant. Data
variables must contain a "units" attribute that is by the plotting routines for
checking and conversion. The "pint" package is used for parsing the units. Some
additional units such as PVU have been added to the package, but failure to
parse the unit will cause the server to disregard the variable. Exemplary valid
units are 'dimensionless', 'hPa', 'm\*\*2', 'm.s^-1', 'millibar', 'knots',
'percent', or 'ppmv'. Please bear in mind that the vertical axis of all vertical
sections is pressure in 'Pa'.

It is assumed that forecast data is given from one initialisation time onward
for several time steps into the future. For each file, the init time is
determined by the units attribute of the "time" variable. The time variable is
identified by its standard_name being "time". The date given after "since" is
interpreted as the init time such that the numerical value of "0" were the init
time (which need not be present in the file). For example, if the units field of
"time" contains "hours since 2012-10-17T12:00:00.000Z", 2012-10-17T12Z would be
the init time. Data for different time steps may be contained in one file or
split over several ones.

In case a file contains additional dimensions beyond the four required ones, MSS
might discard the file, if they are inconsistently used among files or are
missing coordinate variables, etc., even though they would not affect the
operation of MSS. One may skip checks on these dimensions in the data access
class by specifying a list of said dimensions in the "skip_dim_check"
constructor parameter.

An exemplary header for a file containing ozone on a vertical pressure
coordinate and a 3-D tropopause would look as follows:

::

    netcdf example_ASIA {
    dimensions:
            press = 13 ;
            lat = 51 ;
            lon = 141 ;
            time = 12 ;
    variables:
            float press(press) ;
                    press:units = "Pa" ;
                    press:positive = "down" ;
                    press:standard_name = "atmosphere_pressure_coordinate" ;
            float lat(lat) ;
                    lat:units = "degrees_north" ;
                    lat:standard_name = "latitude" ;
            float lon(lon) ;
                    lon:units = "degrees_east" ;
                    lon:standard_name = "longitude" ;
            float time(time) ;
                    time:units = "hours since 2012-10-17T12:00:00Z" ;
                    time:standard_name = "time" ;
            float O3(time, press, lat, lon) ;
                    O3:units = "mol/mol" ;
                    O3:standard_name = "mole_fraction_of_ozone_in_air" ;
            float tropopause(time, lat, lon) ;
                    tropopause:units = "Pa" ;
                    tropopause:standard_name = "tropopause_air_pressure" ;
    }

.. _apache-deployment:


Additional plotting layers
--------------------------

The plotting of data is organised via classes following the abstract base class
Abstract2DSectionStyle in mslib.mswms.mss_2D_sections. One can define a new
class derived from this (respectively the VS_GenericStyle and HS_GenericStyle
classes for vertical and horizontal cross-sections) and add them to the configuration
as shown in the example mswms server configuration files.


Generic plotting layers
.......................

Often a simple plot is sufficient. To facilitate the addition of simple plots, a
generic plotting layer class has been defined. The mslib.mswms.generics module
offers a 'register_standard_name' function that will register a data product
with given CF standard_name (including also units to be used and further
configuration options). In case that the generics module is imported and a style
is registered before the remainder of mslib is imported, plotting classes are
automatically generated. This is demonstrated in the following excerpt from a
mswms settings file::

    # import generics module *first* and register all desired standard_names
    import mslib.mswms.generics as generics
    generics.register_standard_name(
        "mole_fraction_of_CH3Br",
        "pmol/mol"
    )
    # ...
    # now import the styles modules and populate the necessary configuration lists
    # (see also above for information about the mswms server settings file)
    import mslib.mswms.mpl_hsec_styles
    register_horizontal_layers = [
        (mslib.mswms.mpl_hsec_styles.HS_GenericStyle_PL_mole_fraction_of_CH3Br, ["mydata"])]

This would register the new standard_name 'mole_fraction_of_CH3Br', which cause
an associated generic plotting class to be instantiated, which can be used later
on in the configuration file. Such classes are generated for all registered
standard_names, many of which are already preconfigured. The naming scheme for
the new classes are `(HS|VS)_GenericStyle_(PL|AL|TL|ML)_<standard_name>`,
whereby HS/VS denotes horizontal and vertical cross-section, respectively,
PL/AL/TL/ML specifies the vertical coordinate of the plot (for which the
corresponding data must be available), and the last part of the class name is
the CF standard_name itself. In the example above, the registering of the
"mole_fraction_of_CH3Br" standard_name would cause a series of classes to be
generated, amongst them the used
"mslib.mswms.mpl_hsec_styles.HS_GenericStyle_PL_mole_fraction_of_CH3Br", which
offers a horizontal cross-section plot of mole_fraction_of_CH3Br on pressure
levels.

In case these simple plots are insufficient, the make_generic_class functions
from the mslib.mswms.mss_hsec_styles and mslib.mswms.mss_vsec_styles modules
used to generate the generic plots offers additional options for further
configuration to simply add, e.g., user defined contours of other variables on
top or use user defined plotting styles to, e.g., change color maps. More
information about the features can be found in the docstrings of these
functions.


Custom plotting layers
.......................

If the generic plotting layers are not sufficient, a dedicated class can be defined,
which allows the use of all matplotlib features. These classes must be derived from the
appropriate abstract base classes and implement the relevant methods.

Here is a simple example for horizontal cross-sections:

  .. literalinclude:: samples/config/mswms/mswms_plotting_layer.py.sample

This plotting layer offers several 2-D data products, which can be selected
using the style. More examples can be found within the source code of the mswms
component.


A taste of WSGI
---------------

(MS)WMS is a WSGI application based on Flask.
You need a WSGI server to run the application, this converts incoming HTTP requests to the WSGI environ,
and outgoing WSGI responses to HTTP responses.


For self hosting have a look on these `platforms <https://flask.palletsprojects.com/en/2.2.x/deploying/>`_.

We describe two examples, Waitress for a pure Python Server and Apache2 using mod_wsgi. On long running systems you may
want to use Apache2 and have a lot features included in the package. With a nginx proxy also a
waitress server can use certificates and supervisord can be used to monitor and control the waitress process.


Waitress
........
Waitress is a production-quality pure-Python WSGI server.

Installing
~~~~~~~~~~
It is easy to configure and runs on CPython on Unix and Windows. ::

   pixi global install waitress

wms.wsgi
~~~~~~~~
A file
**/home/mss/INSTANCE/wsgi/wsgi_setup.py**
with the content ::

    import sys


    sys.path.insert(0, '/home/mss/INSTANCE/config/where_mswms_settings.py_is/')
    import logging
    logging.basicConfig(stream=sys.stderr)

    from mslib.mswms.wms import app


Running the waitress server
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This runs the wms server on port 5000. If you use a certificate and proxy by e.g. nginx use --url-scheme=https ::

    PYTHONPATH=~/INSTANCE/wsgi/ waitress-serve --host 127.0.0.1 --port 5000 --url-scheme=http wsgi_setup:app

Further documentations:

- `Waitress <https://docs.pylonsproject.org/projects/waitress/en/stable/index.html>`_
- `Waitress as Flask server WSGI <https://www.youtube.com/watch?v=tovsUQu6kBU>`_
- `How to run a Flask App Over HTTPS, using Waitress and NGINX. <https://dev.to/thetrebelcc/how-to-run-a-flask-app-over-https-using-waitress-and-nginx-2020-235c>`_
- `Supervisor: A Process Control System <http://supervisord.org/>`_

Apache server setup
...................

Install mod_wsgi
~~~~~~~~~~~~~~~~

On some distributions an old mod_wsgi is shipped and have to become replaced by
a version compatible to the conda environment. This procedure may need the
package apache2-dev on your server.

At current state we have to use pip to install mod_wsgi into the INSTANCE environment::

  # Install `mod_wsgi`
  $ cd MSS
  $ pixi shell
  $ pixi add mod_wsgi --pypi

  # Find the full path to installed `mod_wsgi`
  $ which mod_wsgi-express

  # Install and register the `mod_wsgi` module with Apache
  $ sudo /full/path/to/installed/mod_wsgi-express install-module


This command outputs two lines::

  LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py3X-x86_64-linux-gnu.so"
  WSGIPythonHome "/home/user/MSS/.pixi/envs/default/bin"


You have to add the lines into your wsgi_express.conf and wsgi_express.load

Setup a /etc/apache2/mods-available/wsgi_express.conf::

  WSGIPythonHome "/home/user/MSS/.pixi/envs/default"


Setup a /etc/apache2/mods-available/wsgi_express.load::

  LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-pyX-x86_64-linux-gnu.so"

Enable the new module by a2enmod and reload the apache2 server

Configuration of apache mod_wsgi.conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One possibility to setup the PYTHONPATH environment variable is by adding it to your mod_wsgi.conf. Alternatively you
could add it also to wms.wsgi.

  WSGIPythonPath /home/mss/INSTANCE/config:/home/user/MSS/.pixi/envs/default/lib/python3.X/site-packages



By this setting you override the PYTHONPATH environment variable. So you have also to add
the site-packes directory of your pixi installation besides the config file path.

If your server hosts different instances by different users you want to setup this path in mswms_setting.py.



One Instance
............

Our examples are based on the following directories located in the home directory of the mss user.
INSTANCE is a placeholder for your service name::

 .
 ├── INSTANCE
 │   ├── config
 │   │   └── mswms_settings.py
 │   │   └── mswms_auth.py
 │   ├── log
 │   │   └── mss_error.log
 │   └── wsgi
 │       ├── auth.wsgi
 │       └── wms.wsgi
 ├── .pixi
 │    ├── .gitignore
 │    └── envs
 │        └── default
 ├── pixi.lock
 └── pixi.toml


Configuration of wsgi for wms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can setup a vhost for this service.

**/home/mss/INSTANCE/wsgi/wms.wsgi**


 .. literalinclude:: samples/wsgi/wms.wsgi




Configuration of wsgi auth
~~~~~~~~~~~~~~~~~~~~~~~~~~

As long as you have only one instance of the server running you can use this method to restrict access.

To restrict access to your data use this script.

**/home/mss/INSTANCE/wsgi/auth.wsgi**


 .. literalinclude:: samples/wsgi/auth.wsgi

This needs also a configuration **/home/mss/INSTANCE/config/mswms_auth.py** script.

 .. literalinclude:: samples/config/mswms/mswms_auth.py.sample


At the moment you have many different instances with different users or different versions of mss you have to use
basic auth of your webserver configuration.


Configuration of your site as vhost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have to setup a webserver server site configuration file

**/etc/apache2/sites-available/mss.yourserver.de.conf**


 .. literalinclude:: samples/sites-available/mss.yourserver.de.conf


Enable it with a2ensite mss.yourserver.de.conf


Many Instances
..............

If you want to setup many instances we suggest to use a similar proxy based configuration

 .. literalinclude:: samples/sites-available/mss_proxy.conf

and if you need authentication then use a Location based AuthType Basic

 .. literalinclude:: samples/sites-available/proxy_demo.yourserver.de.conf



For further information on apache2 server setup read
`<https://httpd.apache.org/docs/2.4/howto/>`_
