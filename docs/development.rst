Development
============================

This chapter will get you started with MSS development.

MSS is written in Python.


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


On top level dir::

  $ git clone https://bitbucket.org/yourfork/mss.git
  $ cd mss
  $ conda create -n mssdev python=2
  $ source activate mssdev
  $ conda build .
  $ conda install --use-local mss
  $ mkdir "$HOME/.config/mss"
  $ # cp mss_settings.json.sample to "$HOME/.config/mss/mss_settings.json"


To install some additional packages needed for running the tests, activate your virtual env and run::

  $ conda install --file requirements.d/development.txt


Running tests
~~~~~~~~~~~~~~~~~~~

We have implemented demodata as data base for testing. On first call of py.test a set of demodata becomes stored
in a /tmp/mss* folder. If you have installed gitpython a postfix of the revision head is added.

::

   $ python -m pytest


Use the -v option to get a verbose result. By the -k option you could select one test to execute only.

A pep8 only test is done by py.test --pep8 -m pep8

Instead of running a ibrary module as a script by the -m option you may also use the py.test command.

::

   $ py.test --cov

This plugin produces a coverage report.

Profiling can be done by e.g.::

   $ python -m cProfile  -s time ./demodata.py > profile.txt


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
* tag the release::

   git tag -s -m "tagged/signed release X.Y.Z" X.Y.Z
   git push origin X.Y.Z

* create a release on anaconda conda-forge
* announce on:
* Mailing list
* Twitter (follow @ReimarBauer for these tweets)

