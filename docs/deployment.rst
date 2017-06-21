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

Per configuration you could register horizontal (*register_horizontal_layers*)
or vertical layers (*register_vertical_layers*), give a basemap
table for EPSG mapping (*epsg_to_mpl_basemap_table*) and at all how to access the data (*nwpaccess*).


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

.. _apache-deployment:

Apache server setup
--------------------------------


Our examples are based on the following directories located in the home directory of the mss user::

 .
 ├── config
 │   └── mss_wms_settings.py
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

To restrict access to your data use this script.

**/home/mss/wsgi/auth.wsgi**


 .. literalinclude:: samples/wsgi/auth.wsgi

This needs also a configuration **/home/mss/config/mss_wms_auth.py** script.

 .. literalinclude:: samples/config/wms/mss_wms_auth.py.sample


Configuration of your site as vhost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have to setup a webserver server site configuration file

**/etc/apache2/sites-available/mss.yourserver.de.conf**


 .. literalinclude:: samples/sites-available/mss.yourserver.de.conf


Enable it with a2ensite mss.yourserver.de.conf


Configuration file of the wms server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

For the standalone server *mswms* you need the path of your mss_wms_settings.py added to the PYTHONPATH. E.g.::

 export PYTHONPATH=/home/mss/config


.. _demodata:

demodata - simulated data
==============================

We provide demodata by executing the demodata programm. This creates in your home directory data files and also
the needed server configuration file. The program creates 70MB of examples.
This script does not overwrite an existing mss_wms_settings.py

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
