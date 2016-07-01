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
For building you have to use the conda recipe localy and install in a new environment::
On top level dir::

  $ git clone https://bitbucket.org/yourfork/mss.git
  $ cd mss
  $ conda build .
  $ conda create -n mssdev  path/to/mss-*.tar.bz2
  $ source activate mssdev
  $ conda install --use-local mss
  $ mkdir "$HOME/.config/mss"
  $ # cp mss_settings.json.sample to "$HOME/.config/mss/mss_settings.json"


To install some additional packages needed for running the tests, activate your virtual env and run::

  $ conda install --file requirements.d/development.txt



Running pep8 tests
~~~~~~~~~~~~~~~~~~~

::

   $ py.test --pep8


Building the docs with Sphinx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation (in reStructuredText format, .rst) is in docs/.

To build the html version of it, you need to have sphinx installed::

   cd docs/
   make html


Then point a web browser at docs/_build/html/index.html.


Creating a new release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* make sure all issues for this milestone are closed or moved to the next milestone
* update CHANGES.rst, based on git log
* check version number of upcoming release in CHANGES.rst
* verify that meta.yaml, MANIFEST.in and setup.py are complete
* tag the release::

   git tag -s -m "tagged/signed release X.Y.Z" X.Y.Z

* create a release on anaconda atmo
* announce on
  * Mailing list
  * Twitter (follow @ReimarBauer for these tweets)

