Installation
=================

Current Releases of mss are based on *python 2*.

We are yet *not ready* for python 3.

Install distributed version by conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Anaconda <https://www.continuum.io/why-anaconda>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on a channel.

 * `conda-forge <https://anaconda.org/conda-forge/mss>`_

The conda-forge packages are based on defaults and other conda-forge packages.
This channel conda-forge has builds for osx-64, linux-64, win-64, win-32.


The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuos integration
build processes.


conda-forge channel
+++++++++++++++++++++

::

   $ conda install -c conda-forge mss

You also could install this project into an environment. ::

   $ conda create -n mssenv python=2
   $ source activate mssenv
   $ conda install -c conda-forge mss





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
* conda install -c conda-forge mss

For a simple test you could start the builtin standalone server by *mswms*.
It should tell::

 serving on http://127.0.0.1:8081

Pointing a browser to
`<http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_
shows the generated XML data the mss app will use.

If you want to look on some data, we provide a demo data set by the program :ref:`demodata`.

For further configuration see :ref:`apache-deployment` or :ref:`mswms-deployment`.
