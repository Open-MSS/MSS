.. _development:


Development
============================

This chapter will get you started with MSS development.

MSS is written in Python.

Once a stable release is published we do only bug fixes in stable and release regulary
new minor versions. If a fix needs a API change or it is likly more a new feature you have
to make a pull request to the develop branch. Documentation of changes is done by using our
`issue tracker <https://bitbucket.org/wxmetvis/mss/issues>`_.

When it is ready the developer version becomes the next stable.


The stable version of MSS is tracked on `BLACK DUCK Open Hub <https://www.openhub.net/p/mss>`_


Style guide
~~~~~~~~~~~~~~~~

We generally follow pep8, with 120 columns instead of 79.

Output and Logging
~~~~~~~~~~~~~~~~~~~~~~~~~

When writing logger calls, always use correct log level (debug only for debugging, info for informative messages,
warning for warnings, error for errors, critical for critical errors/states).

Setup a development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to contribute make a fork on bitbucket of `mss <https://bitbucket.org/wxmetvis/mss>`_.

In the mss package is some demodata included. The default where this is stored is $HOME/mss. Your clone of the
mss repository needs a different folder, e.g. workspace/mss. Avoid to mix data and source.

Some of used packages are in the conda-forge channel located, so we have to add this channel to the default::

  $ conda config --add channels conda-forge
  $ conda config --add channels defaults

Your content of the .condarc config file should have defaults on top::

  $ more $HOME/.condarc
  channels:
  - defaults
  - conda-forge

Create an environment and install the whole mss package dependencies then remove the mss package::

  $ conda create -n mssdev python=3
  $ conda activate mssdev
  $ conda install mamba
  $ mamba install mss
  $ conda remove mss --force


You can also use conda to install mss, but mamba is a way faster.
Compare versions used in the meta.yaml between stable and develop branch and apply needed changes.

Add the path of your local cloned mss directory to $PYTHONPATH.

For developer we provide additional packages for running tests, activate your env and run::

  $ conda install --file requirements.d/development.txt

On linux install the `conda package pyvirtualdisplay` and `xvfb` from your linux package manager.
This is used to run tests on a virtual display.
If you don't want tests redirected to the xvfb display just setup an environment variable::

 $ export TESTS_VISIBLE=TRUE


Setup demodata
~~~~~~~~~~~~~~

:ref:`demodata` is provided by executing::

   $(mssdev) python mslib/mswms/demodata.py --create

To use this data add the mss_wms_settings.py in your python path::

   $(mssdev) cd $HOME/PycharmProjects/mss
   $(mssdev) export PYTHONPATH="`pwd`:$HOME/mss"
   $(mssdev) python mslib/mswms/mswms.py

Developer Documentation of Mscolab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Mscolab server is built using the Flask rest framework which communicates with the PyQt5 frontend of MSS.
You can view the default configuration of mscolab in the file `mslib/mscolab/conf.py`.
If you want to change any values of the configuration, please take a look at the "Configuring Your Mscolab Server"
section in :ref:`mscolab`

When using for the first time you need to initialise your database. Use the command :code:`python mslib/mscolab/mscolab db --init` to initialise it. The default database is a sqlite3 database.
You can add some dummy data to your database by using the command :code:`python mslib/mscolab/mscolab.py db --seed`.
The content of the dummy data can be found in the file `mslib/mscolab/seed.py`.

To start your server use the command :code:`python mslib/mscolab/mscolab.py start`. This would start the mscolab server on port 8083.
Going to http://localhost:8083/ should now show "Mscolab server". This means your server has started successfully.
Now you can use the MSS desktop application to connect to it using the Mscolab window of the application.


Running tests
~~~~~~~~~~~~~~~~~~~

We have implemented demodata as data base for testing. On first call of pytest a set of demodata becomes stored
in a /tmp/mss* folder. If you have installed gitpython a postfix of the revision head is added.

::

   $ pytest


Use the -v option to get a verbose result. By the -k option you could select one test to execute only.

A pep8 only test is done by `py.test --pep8 -m pep8`  or `pytest --pep8 -m pep8`

Instead of running a ibrary module as a script by the -m option you may also use the pytest command.

::

   $ pytest --cov mslib

This plugin produces a coverage report, example::

    ----------- coverage: platform linux, python 3.7.3-final-0 -----------
    Name                                     Stmts   Miss Branch BrPart  Cover
    --------------------------------------------------------------------------
    mslib/__init__.py                            2      0      0      0   100%
    mslib/msui/__init__.py                      23      0      0      0   100%
    mslib/msui/aircrafts.py                     52      1      8      1    97%
    mslib/msui/constants.py                     12      2      4      2    75%
    mslib/msui/flighttrack.py                  383    117    141     16    66%


Profiling can be done by e.g.::

   $ python -m cProfile  -s time ./mslib/mswms/demodata.py > profile.txt

example::

    /!\ existing server config: "mss_wms_settings.py" for demodata not overwritten!


    To use this setup you need the mss_wms_settings.py in your python path e.g.
    export PYTHONPATH=$HOME/mss
             398119 function calls (389340 primitive calls) in 0.834 seconds

       Ordered by: internal time

       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
           19    0.124    0.007    0.496    0.026 demodata.py:912(generate_file)
           19    0.099    0.005    0.099    0.005 {method 'close' of 'netCDF4._netCDF4.Dataset' objects}



Setup mss_settings.json
----------------------------

On default all tests use default configuration defined in mslib.msui.MissionSupportSystemDefaultConfig.
If you want to overwrite this setup and try out a special configuration add an mss_settings.json
file to the testings base dir in your tmp directory.


Building the docs with Sphinx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation (in reStructuredText format, .rst) is in docs/.

To build the html version of it, you need to have sphinx installed::

   cd docs/
   make html


Then point a web browser at docs/_build/html/index.html.

Update local stable branch
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't have a stable branch, create one first or change to that branch::

   git checkout [-b] stable
   git pull git@bitbucket.org:wxmetvis/mss.git stable
   git push


Merging stable into develop
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bug fixes we have done in stable we need to merge regulary into develop too:: 

    git checkout stable
    git pull
    git checkout develop
    git pull
    git merge stable


Testing local build
~~~~~~~~~~~~~~~~~~~

We provide in the dir localbuild the setup which will be used as a base on conda-forge to build mss.
As developer you should copy this directory and adjust the source path, build number.

using a local meta.yaml recipe::

  $ cd yourlocalbuild
  $ conda build .
  $ conda create -n mssbuildtest
  $ conda activate mssbuildtest
  $ conda install --use-local mss


Take care on removing alpha builds, or increase the build number for a new version.


Creating a new release
~~~~~~~~~~~~~~~~~~~~~~

* make sure all issues for this milestone are closed or moved to the next milestone
* update CHANGES.rst, based on git log
* check version number of upcoming release in CHANGES.rst
* verify that version.py, meta.yaml, MANIFEST.in and setup.py are complete
* for a new stable release merge from develop to stable
* tag the release::

   git tag -s -m "tagged/signed release X.Y.Z" X.Y.Z
   git push origin X.Y.Z

* create a release on anaconda conda-forge
* announce on:
* Mailing list
* Twitter (follow @TheMSSystem for these tweets)


Publish on Conda Forge
~~~~~~~~~~~~~~~~~~~~~~

* update a fork of the `mss-feedstock <https://github.com/conda-forge/mss-feedstock>`_
  - set version string
  - set sha256 checksum of the tagged release
  - update dependencies

* rerender the feedstock by conda smithy
* send a pull request
* maintainer will merge if there is no error

