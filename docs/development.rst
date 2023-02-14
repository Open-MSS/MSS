.. _development:

Development
===========

This chapter will get you started with MSS development.

MSS is written in Python.

Once a stable release is published we do only bug fixes in stable and release regulary
new minor versions. If a fix needs a API change or it is likly more a new feature you have
to make a pull request to the develop branch. Documentation of changes is done by using our
`issue tracker <https://github.com/Open-MSS/MSS/issues>`_.

When it is ready the developer version becomes the next stable.


The stable version of MSS is tracked on `BLACK DUCK Open Hub <https://www.openhub.net/p/mss>`_

Using our Issue Tracker on github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How to Report Bugs
-------------------

Please open a new issue in the appropriate GitHub repository `here <https://github.com/Open-MSS/MSS/issues/new>`_ with steps to reproduce the problem you're experiencing.

Be sure to include as much information including screenshots, text output, and both your expected and actual results.

How to Request Enhancements
---------------------------

First, please refer to the applicable `GitHub repository <https://github.com/Open-MSS/MSS>`_ and search `the repository's GitHub issues <https://github.com/Open-MSS/MSS/issues>`_ to make sure your idea has not been (or is not still) considered.

Then, please `create a new issue <https://github.com/Open-MSS/MSS/issues/new>`_ in the GitHub repository describing your enhancement.

Be sure to include as much detail as possible including step-by-step descriptions, specific examples, screenshots or mockups, and reasoning for why the enhancement might be worthwhile.



Setting Up a Local Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requirements
------------

1. System requirements

  | Any system with basic configuration.
  | Operating System : Any (Windows / Linux / Mac).

2. Software requirement

  | Python
  | `Additional Requirements <https://github.com/Open-MSS/MSS/blob/develop/requirements.d/development.txt>`_


3. Skill set

  | Knowledge of git & github
  | python

Forking the Repo
----------------

1. Firstly you have to make your own copy of project. For that you have to fork the repository. You can find the fork button on the top-right side of the browser window.

2. Kindly wait till it gets forked.

3. After that copy will look like *<your-user-name>/MSS* forked from *Open-MSS/MSS*.

Cloning the Repo
----------------

1. Now you have your own copy of project. Here you have to start your work.

2. Go to desired location on your computer where you want to set-up the project.

3. Right click there and click on git bash. A terminal window will pop up

4. Click The big green button which says "Code". Copy the URL. `Like this <https://user-images.githubusercontent.com/71402528/122255281-9a855d80-ceeb-11eb-9f85-fed38db30562.png>`_

5. Now Type the command ``git clone <your-fork-url>.git`` and hit enter. Also, you could use ``gh repo clone <repo-owner>/<repo-name>``, If you don't have ``gh``, see this for installation `here <https://github.com/cli/cli/blob/trunk/docs/install_linux.md>`_.

6. Wait for few seconds till the project gets copied

  or simply head over here for `cloning a repository <https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository>`_

7. Add the path of your local cloned mss directory to $PYTHONPATH.

Setting up a git remote
-----------------------

1. Now you have to set up remote repositories
2. Type ``git remote -v`` in terminal to list remote connections to your repo.
3. It will show something like this::

     origin  git@github.com:<your-user-name>/MSS.git (fetch)
     origin  git@github.com:<your-user-name>/MSS.git (push)

4. Add an upstream remote by the command ::

     git remote add upstream git@github.com:Open-MSS/MSS.git



5. Again type in command ``git remote -v`` to check if remote has been set up correctly
6. It should show something like this ::

     origin	git@github.com:<your-user-name>/MSS.git (fetch)
     origin	git@github.com:<your-user-name>/MSS.git (push)
     upstream	git@github.com:Open-MSS/MSS.git (fetch)
     upstream	git@github.com:Open-MSS/MSS.git (push)

Update local stable branch
--------------------------

If you don't have a stable branch, create one first or change to that branch::


  git checkout [-b] stable
  git pull git@github.com:Open-MSS/MSS.git stable
  git push



Installing dependencies
-----------------------

MSS is based on the software of the conda-forge channel located, so we have to add this channel to the default::


  $ conda config --add channels conda-forge

Your content of the .condarc config file should have conda-forge on top::

  $ more $HOME/.condarc
  channels:
  - conda-forge
  - defaults

Create an environment and install the whole mss package dependencies then remove the mss package::

  $ conda create -n mssdev mamba
  $ conda activate mssdev
  $ mamba install mss=$mss_version python --only-deps

You can also use conda to install mss, but mamba is a way faster.
Compare versions used in the meta.yaml between stable and develop branch and apply needed changes.

Setup mswms server
++++++++++++++++++

In the mss package is some demodata included. The default where this is stored is $HOME/mss. Your clone of the
MSS repository needs a different folder, e.g. workspace/mss. Avoid to mix data and source.

:ref:`demodata` is provided by executing::

   $(mssdev) python mslib/mswms/demodata.py --seed

To use this data add the mswms_settings.py in your python path::

   $(mssdev) cd $HOME/PycharmProjects/mss
   $(mssdev) export PYTHONPATH="`pwd`:$HOME/mss"
   $(mssdev) python mslib/mswms/mswms.py

Setup mscolab server
++++++++++++++++++++

The Mscolab server is built using the Flask rest framework which communicates with the PyQt5 frontend of MSS.
You can view the default configuration of mscolab in the file `mslib/mscolab/conf.py`.
If you want to change any values of the configuration, please take a look at the "Configuring Your Mscolab Server"
section in :ref:`mscolab`

When using for the first time you need to initialise your database. Use the command :code:`python mslib/mscolab/mscolab.py db --init`
to initialise it. The default database is a sqlite3 database.
You can add some dummy data to your database by using the command :code:`python mslib/mscolab/mscolab.py db --seed`.
The content of the dummy data can be found in the file `mslib/mscolab/seed.py`.

To start your server use the command :code:`python mslib/mscolab/mscolab.py start`. This would start the mscolab server on port 8083.
Going to http://localhost:8083/status should now show "Mscolab server". This means your server has started successfully.
Now you can use the MSS desktop application to connect to it using the Mscolab window of the application.

Setup local testing
+++++++++++++++++++

With sending a Pull Request our defined CIs do run all tests on github.
You can do run tests own system too.

For developers we provide additional packages for running tests, activate your env and run::

  $ mamba install --file requirements.d/development.txt

On linux install the `conda package pyvirtualdisplay` and `xvfb` from your linux package manager.
This is used to run tests on a virtual display.
If you don't want tests redirected to the xvfb display just setup an environment variable::

 $ export TESTS_VISIBLE=TRUE

We have implemented demodata as data base for testing. On first call of pytest a set of demodata becomes stored
in a /tmp/mss* folder. If you have installed gitpython a postfix of the revision head is added.


Setup msui_settings.json for special tests
+++++++++++++++++++++++++++++++++++++++++

On default all tests use default configuration defined in mslib.msui.MissionSupportSystemDefaultConfig.
If you want to overwrite this setup and try out a special configuration add an msui_settings.json
file to the testings base dir in your tmp directory. You call it by the custom `--msui_settings` option


Testing
-------

After you installed the dependencies for testing you could invoke the tests by `pytest` with various options.

Run Tests
+++++++++

Our tests are using the pytest framework. You could run tests serial and parallel

::

   $ pytest tests

or parallel

::

  $ pytest -n auto --dist loadscope --max-worker-restart 0 tests

Use the -v option to get a verbose result. By the -k option you could select one test to execute only.

Verify Code Style
+++++++++++++++++

A flake8 only test is done by `py.test --flake8 -m flake8`  or `pytest --flake8 -m flake8`

Instead of running a ibrary module as a script by the -m option you may also use the pytest command.

Coverage
++++++++

::

   $ pytest --cov mslib tests

This plugin produces a coverage report, example::

    ----------- coverage: platform linux, python 3.7.3-final-0 -----------
    Name                                     Stmts   Miss Branch BrPart  Cover
    --------------------------------------------------------------------------
    mslib/__init__.py                            2      0      0      0   100%
    mslib/msui/__init__.py                      23      0      0      0   100%
    mslib/msui/aircrafts.py                     52      1      8      1    97%
    mslib/msui/constants.py                     12      2      4      2    75%
    mslib/msui/flighttrack.py                  383    117    141     16    66%


Profiling
+++++++++

Profiling can be done by e.g.::

   $ python -m cProfile  -s time ./mslib/mswms/demodata.py --seed > profile.txt

example::

   /!\ existing server config: "mswms_settings.py" for demodata not overwritten!


   /!\ existing server auth config: "mswms_auth.py" for demodata not overwritten!


   To use this setup you need the mswms_settings.py in your python path e.g.
   export PYTHONPATH=~/mss
         557395 function calls (543762 primitive calls) in 0.980 seconds

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       23    0.177    0.008    0.607    0.026 demodata.py:1089(generate_file)
      631    0.113    0.000    0.230    0.000 demodata.py:769(_generate_3d_data)
      179    0.077    0.000    0.081    0.000 {method 'createVariable' of 'netCDF4._netCDF4.Dataset' objects}



Pushing your changes
--------------------

1. Now you have made the changes, tested them and built them. So now it's time to push them.
2. Goto your terminal and type git status and hit enter, this will show your changes from the files
3. Then type in git add and hit enter, this will add all the files to staging area
4. Commit the changes by ``git commit -m "<message-describing-your-change>"`` and hit enter.
5. Now push your branch to your fork by ``git push origin <your-branch-name>`` and hit enter.


Creating a pull request
-----------------------

By this time you can see a message on your github fork as your fork is ahead of Open-MSS:develop by <number> of commits and also you can see a button called Compare and pull request.

Click on Compare and pull request button.

You will see a template.

Fill out the template completely by describing your change, cause of change, issue getting fixed etc.

After filling the template completely click on Pull request


Guides
~~~~~~

Code Style
----------

We generally follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_, with 120 columns instead of 79.

Output and Logging
------------------

When writing logger calls, always use correct log level (debug only for debugging, info for informative messages,
warning for warnings, error for errors, critical for critical errors/states).

Building the docs with Sphinx
-----------------------------

The documentation (in reStructuredText format, .rst) is in docs/.

To build the html version of it, you need to have sphinx installed::

   cd docs/
   make html


Then point a web browser at docs/_build/html/index.html.


Merging stable into develop
---------------------------

Bug fixes we have done in stable we need to merge regulary into develop too::

   git checkout stable
   git pull git@github.com:Open-MSS/MSS.git stable
   git checkout develop
   git pull git@github.com:Open-MSS/MSS.git develop
   git merge stable
   git checkout -b develop_stable
   git push git@github.com:Open-MSS/MSS.git develop_stable


Then create the proposed merge request. The merge request must *not* be squashed or rebased.
To allow the merging, the requirement for a linear-history must be disabled *temporarily*
for the develop branch and one needs to ensure that the merge request is accepted with a
regular merge with merge commit. Remove the develop_stable branch if still present.


Testing local build
-------------------

We provide in the dir localbuild the setup which will be used as a base on conda-forge to build mss.
As developer you should copy this directory and adjust the source path, build number.

using a local meta.yaml recipe::

  $ cd yourlocalbuild
  $ conda build .
  $ conda create -n mssbuildtest mamba
  $ conda activate mssbuildtest
  $ mamba install --use-local mss


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

* write a release information on https://github.com/Open-MSS/MSS/releases
* create a release on anaconda conda-forge
* announce on:

  * Mailing list
  * Twitter (follow @TheMSSystem for these tweets)



Publish on Conda Forge
----------------------

* update a fork of the `mss-feedstock <https://github.com/conda-forge/mss-feedstock>`_
  - set version string
  - set sha256 checksum of the tagged release
  - update dependencies

* rerender the feedstock by conda smithy
* send a pull request
* maintainer will merge if there is no error


Google Summer of Code(TM)
~~~~~~~~~~~~~~~~~~~~~~~~~
MSS takes part in Google Summer of Code
as a sub-organization of Python Software Foundation(PSF).

GSoC'22 Projects
----------------

- `Sreelakshmi Jayarajan: Automated Command Line Plotting Tool : GSoC 2022 <https://github.com/Open-MSS/MSS/wiki/Automated-Command-Line-Plotting-Tool-:-GSoC-2022>`_

- `Jatin Jain: UI and server improvements GSOC 2022 <https://github.com/Open-MSS/MSS/wiki/UI-and-server-improvements-GSOC-2022>`_


GSoC'21 Projects
----------------

- `Hrithik Kumar Verma: Generating a tool chain tutorial for the MSUI user interface by automation operations : GSoC 2021 <https://github.com/Open-MSS/MSS/wiki/Generating-a-tool-chain-tutorial-for-the-MSUI-user-interface-by-automation-operations-:-GSoC---2021>`_

- `Aravind Murali: MSUI: UI Redesign GSOC 2021 <https://github.com/Open-MSS/MSS/wiki/MSUI:-UI-Redesign---GSOC-2021>`_


GSoC'20 Projects
----------------

- `Aryan Gupta: Mission Support System : Enhance KML Support <https://github.com/Open-MSS/MSS/wiki/KML:-Enhance-KML-Support---GSoC-2020>`_

- `Tanish Grover: Mission Support System: Mission Support Collaboration Improvements <https://github.com/Open-MSS/MSS/wiki/Mscolab:-Mission-Support-Collaboration-Improvements---GSoC-2020>`_

GSoC'19 Projects
----------------

- `Anveshan Lal: Updating Geographical Plotting Routines <https://github.com/Open-MSS/MSS/wiki/Cartopy:-Updating-Geographical-Plotting-Routines----GSoC-2019>`_

- `Shivashis Padhi: Collaborative editing of flight path in real-time <https://github.com/Open-MSS/MSS/wiki/Mscolab:-Collaborative-editing-of-flight-path-in-real-time---GSoC19>`_

