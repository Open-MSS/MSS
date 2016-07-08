
Installation
=================

Install distributed version by conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Anaconda <https://www.continuum.io/why-anaconda>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a
modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on `atmo <https://anaconda.org/atmo/mss>`_
channel of anaconda::

   $ conda install -c atmo mss=1.2.0


You also could install this project into an environment. ::

   $ conda create -n mssenv python=2
   $ source activate mssenv
   $ conda install -c atmo mss=1.2.0


For further details :ref:`mss-configuration`

Server based installation using miniconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a wms server setup you may want to have a dedicated user running mswms or the apache2 wsgi script.
We suggest to create a mss user.

* create a mss user on your system
* login as mss user
* create a *src* directory in /home/mss
* cd src
* get `miniconda <http://conda.pydata.org/miniconda.html>`_ for Python 2
* set execute bit on install script
* execute script, enable environment in .bashrc
* login again or export PATH="/home/mss/miniconda2/bin:$PATH"
* python --version should tell Python 2.7.12
* conda install -c atmo mss=1.2.0

For a simple test you could start the builtin standalone server by *mswms*.
It should tell::

 serving on http://127.0.0.1:8081

Pointing a browser to
`<http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_
shows the generated XML data the mss app will use.

For further configuration see :ref:`apache-deployment`.
