wms - Web Map Service
=====================================

Once installation and configuration are complete, you can start the
Web Map Service application (provided you have forecast data to visualise).
The file "mswms" is an executable Python script starting up a Paste HTTP server
with the WMS WSGI module.
A short description of how to start the program is given by the --help option.
The file "wms.wsgi" is intended to be used with an Apache web server
installation.

We have methods to use data for ECMWF, CLaMS, GWFC, EMAC, METEOSAT implemented.
The data have to use for their parameters the CF attribute standard_name.
A new method should be able to deal with any CF conforming file following a
couple of simple additional requirements.

Per configuration you could register horizontal (*register_horizontal_layers*)
or vertical layers (*register_vertical_layers*), give a basemap
table for EPSG mapping (*epsg_to_mpl_basemap_table*) and at all how to access the data.


A few notes:

- If you run the Paste WMS on a remote machine (e.g. on your office
  computer which you access via ssh from a campaign site), consider
  the ssh-tunnel option. Create the ssh connection with the "-L"
  option and start the WMS with the tunneled port as option.

- The Paste WMS currently cannot run multithreaded (Apache does
  support multiple processes). This is due to that a single instance
  of the WSGI application handler class MSS_WMSResponse can create
  only one plot at a time (otherwise you get messed up plots when
  simultaneous requests occur). In the current implementation, only a
  single instance is passed to PASTE (to do all the initialisation
  work only once. To extend the software to handle simultaneous
  requests would probably involve creating a "factory" of
  MSS_WMSResponse instances.. If you want to do this, check if/how
  PASTE handles "worker" factories.

- Creating the capabilities document can take very long (> 1 min) if
  the forecast data files have to be read for the first time (the WMS
  program opens all files and tries to determine the available data
  and elevation ranges). Once the information used for the
  capabilities are in the cache, however, a GetCapabilities request
  should return a document within 1-2 seconds.

- A typical bottleneck for plot generation is when the forecast data
  files are located on a different computer than the WMS server. In
  this case, large amounts of data have to be transferred over the
  network. Hence, when possible, try to make sure the WMS runs on the
  same computer on which the input data files are hosted.



Configuration file of the wms server
------------------------------------

Configuration for the Mission Support System Web Map Service (wms).

In this module the data organisation structure of the available forecast
data is described. The class NWPDataAccess is subclassed for each data type
in the system and provides methods to determine which file needs to be accessed for a given variable and time.
The classes also provide methods to query the available initialisation times for a given variable,
and the available valid times for a variable and a given initialisation time. As the latter methods need
to open the NetCDF data files to determine the contained time values, a caching system is used to avoid
re-opening already searched files.


The configuration file have to become added to the /home/mss/config directory

**/home/mss/config/mss_wms_settings.py**

 .. literalinclude:: samples/config/wms/mss_wms_settings.py.sample


You have to adopt this file to your data.


.. _mswms-deployment:

Standalone server setup
------------------------------

For the standalone server *mswms* you need the path of your mss_wms_settings.py and other configuration files
added to the PYTHONPATH. E.g.::

 export PYTHONPATH=/home/mss/config


.. _meteo_data:

meteorological data
--------------------

Data for the MSS server shall be provided in CF-compliant NetCDF format.
Several specific data access methods are provided for ECMWF, Meteoc, and several other formats.

The prefered method "AutomaticDataAccess" shall supplant most of these, but requires the data
to be organised in the fashion described in the following (the others pose mostly the same
requirements).

All data files belonging to one "set" shall have a common string in its name that can be used to uniquely
identify all files of this set. Each set must share
the same time, longitude, and latitude grid. Each set must use the same elevation layers for each type of
vertical axis. Different data sets may be used to offer different
geographical regions or results of different simulation models.

Each file of a set must contain only one or no vertical axis. If
the data is required to be given on multiple vertical axis (such as providing data
for horizontal plots on both pressure and theta levels), one (or more separate) file for each
vertical axis type must be provided. All files for one axis type shall provide the same levels.
If no vertical axis can be identified, it is assumed that the file contains 3-D data (time, lat, lon)
such as, e.g., surface pressure or tropopause altitude.

The vertical coordinate variable is identified by the standard_name being one of the following names:

- atmosphere_hybrid_sigma_pressure_coordinate - "ml"

- atmosphere_pressure_coordinate - "pl"

- atmosphere_ertel_potential_vorticity_coordinate - "pv"

- atmosphere_altitude_coordinate - "al"

- atmosphere_potential_temperature_coordinate - "tl"

The two-letter abbreviation is used for brief identification in the plotting routines in addition
to the standard_name of the variable to uniquely identify which data shall be used.
The data shall be organized with the dimensions in the order of "time", "vertical coordinate",
"latitudes", and "longitudes" (This is important to reduce disk access when generating the plots).
Data variables are identified by their standard_name, which is expected to be CF compliant.
Data variables should contain a "units" attribute that may be used by the plotting routines
for checking and/or conversion. Please bear in mind that the vertical axis of all vertical
sections is pressure in 'Pa'.

It is assumed that forecast data is given from one initialisation time onward for several time steps
into the future. For each file, the init time is determined by the units attribute of the "time"
variable. The time variable is identified by its standard_name being "time".
The date given after "since" is interpreted as the init time such that the numerical value
of "0" were the init time (which need not be present in the file).
For example, if the units field of "time" contains "hours since 2012-10-17T12:00:00.000Z", 2012-10-17T12Z would
be the init time. Data for different time steps may be contained in one file or split over several ones.

An exemplary header for a file containing ozone on a vertical pressure coordinate and a 3-D tropopause
would look as follows:

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


.. _demodata:


demodata - simulated data
--------------------------

We provide demodata by executing the demodata programm. This creates in your home directory data files and also
the needed server configuration files. The program creates 70MB of examples. All generated files follow the
guidelines given above. This script does not overwrite an existing mss_wms_settings.py

::

  mss
  ├── mss_wms_auth.py
  ├── mss_wms_settings.py
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



Detailed server configuration *mss_wms_settings.py* for this demodata

 .. literalinclude:: samples/config/wms/mss_wms_settings.py.demodata

For setting authentication see *mss_wms_auth.py*

 .. literalinclude:: samples/config/wms/mss_wms_auth.py.sample



.. _apache-deployment:


Apache server setup
-------------------

One Instance
............

Our examples are based on the following directories located in the home directory of the mss user::

 .
 ├── config
 │   └── mss_wms_settings.py
 |   └── mss_wms_data_access_settings.py
 |   └── mss_wms_auth.py
 ├── log
 │   └── mss_error.log
 ├── miniconda2
 │   ├── bin
 │   ├── conda-bld
 │   ├── conda-meta
 │   ├── envs
 │   ├── etc
 │   ├── include
 │   ├── lib
 │   ├── LICENSE.txt
 │   ├── pkgs
 │   ├── share
 │   ├── ssl
 │   └── var
 └── wsgi
     ├── auth.wsgi
     └── wms.wsgi


Create that mss user first.



Configuration of apache mod_wsgi.conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One posibility to setup the PYTHONPATH environment variable is by adding it to your mod_wsgi.conf. Alternativly you
could add it also to mss_wms_settings.py.

  WSGIPythonPath /home/mss/config:/home/mss/miniconda2/lib/python2.7/site-packages


By this setting you override the PYTHONPATH environment variable. So you have also to add
the site-packes directory of your miniconda or anaconda installation besides the config file path.

If your server hosts different instances by different users you want to setup this path in mss_wms_setting.py.


Configuration of wsgi for wms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can setup a vhost for this service.

**/home/mss/wsgi/wms.wsgi**


 .. literalinclude:: samples/wsgi/wms.wsgi




Configuration of wsgi auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As long as you have only one instance of the server running you can use this method to restrict access.

To restrict access to your data use this script.

**/home/mss/wsgi/auth.wsgi**


 .. literalinclude:: samples/wsgi/auth.wsgi

This needs also a configuration **/home/mss/config/mss_wms_auth.py** script.

 .. literalinclude:: samples/config/wms/mss_wms_auth.py.sample


At the moment you have many different instances with different users or different versions of mss you have to use
basic auth of your webserver configuration.



Configuration of your site as vhost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have to setup a webserver server site configuration file

**/etc/apache2/sites-available/mss.yourserver.de.conf**


 .. literalinclude:: samples/sites-available/mss.yourserver.de.conf


Enable it with a2ensite mss.yourserver.de.conf


Many Instances
..............

If you want to setup many instances we suggest to use a similiar proxy based configuration

 .. literalinclude:: samples/sites-available/mss_proxy.conf

and if you need authentication then use a Location based AuthType Basic

 .. literalinclude:: samples/sites-available/proxy_demo.yourserver.de.conf



For further informations on apache2 server setup read `<https://httpd.apache.org/docs/2.4/howto/>`_
