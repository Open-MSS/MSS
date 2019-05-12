Development
============================

This chapter will get you started with MSS development.

MSS is written in Python.

Once a stable release is published we do only bug fixes in stable and release regulary
new minor versions. If a fix needs a API change or it is likly more a new feature you have
to make a pull request to the develop branch. Documentation of changes is done by using our
`issue tracker <https://bitbucket.org/wxmetvis/mss/issues>`_.

When it is ready the developer version becomes the next stable.


Style guide
~~~~~~~~~~~~~~~~

We generally follow pep8, with 120 columns instead of 79.

Output and Logging
~~~~~~~~~~~~~~~~~~~~~~~~~

When writing logger calls, always use correct log level (debug only for debugging, info for informative messages,
warning for warnings, error for errors, critical for critical errors/states).

Building a development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to contribute make a fork on bitbucket of `mss <https://bitbucket.org/wxmetvis/mss>`_.
For building you have to use the conda recipe localy and install in a new environment.

Some of used packages are in the conda-forge channel located, so we have to add this channel to the default::

  $ conda config --add channels conda-forge

Or add the channel by an editor to the .condarc config file::

  $ more ~/.condarc
  channels:
  - defaults
  - conda-forge


using a local meta.yaml recipe::

  $ git clone https://bitbucket.org/yourfork/mss.git
  $ cd mss
  $ conda create -n mssdev python=3
  $ conda activate mssdev
  $ conda build .
  $ conda install --use-local mss
  $ mkdir "$HOME/.config/mss"
  $ # cp mss_settings.json.sample to "$HOME/.config/mss/mss_settings.json"
  $ conda remove mss


alternative get the whole package first::

 $ conda create -n mssdev mss
 $ conda activate mssdev
 $ conda remove mss

Compare versions used in the meta.yaml between stable and develop branch and apply needed changes.

Add the path of your local cloned mss directory to $PYTHONPATH.

Add developer packages for running tests, activate your env and run::

  $ conda install --file requirements.d/development.txt

On linux install `xvfb` from your linux package manager. This is used to run tests on a virtual display.

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
    export PYTHONPATH=~/mss
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
* Twitter (follow @ReimarBauer for these tweets)

