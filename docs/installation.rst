Installation
=================

Current Releases of mss are based on python2.

Install distributed version by conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Anaconda <https://www.continuum.io/why-anaconda>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on two channels.

 * `atmo <https://anaconda.org/atmo/mss>`_
 * `conda-forge <https://anaconda.org/conda-forge/mss>`_

The atmo channel has builds for win-64 and linux-64 and is based on anacondas default packages.
And conda-forge packages are based on defaults and other conda-forge packages. So conda-forge has builds for ios-64, linux-64, win-64, win-32.

You can choose between both channels dependent on your operation system,
IOS will need the build package from conda-forge.

`conda-forge <https://conda-forge.github.io/>`_ uses various automated continuos integration
build processes.

atmo channel
++++++++++++++++

::

   $ conda install -c atmo mss=1.2.2


You also could install this project into an environment. ::

   $ conda create -n mssenv python=2
   $ source activate mssenv
   $ conda install -c atmo mss=1.2.2


conda-forge channel
+++++++++++++++++++++

::

   $ conda install -c conda-forge mss=1.2.2

You also could install this project into an environment. ::

   $ conda create -n mssenv python=2
   $ source activate mssenv
   $ conda install -c conda-forge mss=1.2.2





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
* conda install -c atmo mss=1.2.2

For a simple test you could start the builtin standalone server by *mswms*.
It should tell::

 serving on http://127.0.0.1:8081

Pointing a browser to
`<http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_
shows the generated XML data the mss app will use.

For further configuration see :ref:`apache-deployment` or :ref:`mswms-deployment`.
