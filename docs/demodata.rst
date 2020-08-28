.. _demodata:


Simulated Data and its configuration
====================================

mswms
~~~~~
We provide demodata by executing the :code:`mswms_demodata` program. This creates in your home directory data files and also
the needed server configuration files. The program creates 70MB of examples.
This script does not overwrite an existing mss_wms_settings.py.

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