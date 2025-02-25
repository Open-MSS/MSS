.. _development:

Development
===========

This chapter will get you started with MSS development.

MSS is written in Python.

Once a stable release is published we do only bug fixes in stable and release regularly
new minor versions. If a fix needs a API change or it is likely more a new feature you have
to make a pull request to the develop branch. Documentation of changes is done by using our
`issue tracker <https://github.com/Open-MSS/MSS/issues>`_.

When it is ready the developer version becomes the next stable.


The stable version of MSS is tracked on `BLACK DUCK Open Hub <https://www.openhub.net/p/mss>`_


Contributing
------------

Please read our `contributing <https://open-mss.github.io/contributing/>`_ guidelines and
`setup instructions <https://open-mss.github.io/develop/Setup-Instructions>`_ to get
started with MSS development.


Using our Issue Tracker on github
---------------------------------

How to Report Bugs
..................

Please open a new issue in the appropriate GitHub repository `https://github.com/Open-MSS/MSS/issues/new <https://github.com/Open-MSS/MSS/issues/new>`_ with steps to reproduce the problem you're experiencing.

Be sure to include as much information including screenshots, text output, and both your expected and actual results.

How to Request Enhancements
...........................

First, please refer to the applicable `GitHub repository <https://github.com/Open-MSS/MSS>`_ and search `the repository's GitHub issues <https://github.com/Open-MSS/MSS/issues>`_ to make sure your idea has not been (or is not still) considered.

Then, please `create a new issue <https://github.com/Open-MSS/MSS/issues/new>`_ in the GitHub repository describing your enhancement.

Be sure to include as much detail as possible including step-by-step descriptions, specific examples, screenshots or mockups, and reasoning for why the enhancement might be worthwhile.


Forking the Repo
----------------

1. Firstly you have to make your own copy of project. For that you have to fork the repository. You can find the fork button on the top-right side of the browser window.

2. Kindly wait till it gets forked.

3. After that copy will look like *<your-user-name>/MSS* forked from *Open-MSS/MSS*.

Cloning the Repo
................

1. Now you have your own copy of project. Here you have to start your work.

2. Go to desired location on your computer where you want to set-up the project.

3. Right click there and click on git bash. A terminal window will pop up

4. Click The big green button which says "Code". Copy the URL. `Like this <https://user-images.githubusercontent.com/71402528/122255281-9a855d80-ceeb-11eb-9f85-fed38db30562.png>`_

5. Now Type the command ``git clone <your-fork-url>.git`` and hit enter. Also, you could use ``gh repo clone <repo-owner>/<repo-name>``, If you don't have ``gh``, see this for installation `here <https://github.com/cli/cli/blob/trunk/docs/install_linux.md>`_.

6. Wait for few seconds till the project gets copied

  or simply head over here for `cloning a repository <https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository>`_

Setting up a git remote
.......................

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
..........................

If you don't have a stable branch, create one first or change to that branch::


  git checkout [-b] stable
  git pull git@github.com:Open-MSS/MSS.git stable
  git push


Setting Up a Local Environment
------------------------------

Requirements
............

1. System requirements

  | Any system with basic configuration.
  | Operating System : Any (Windows / Linux / Mac).

2. Software requirement

  | `Pixi <https://pixi.sh/>`_

3. Skill set

  | Knowledge of git & github
  | Python


Software environment for development
....................................

The dependencies necessary to get a working development environment for MSS are specified in pixi.toml and pixi.lock.
This means you can get a shell with all required packages installed using::

    pixi shell -e dev

Afterwards, a call to e.g.::

    msui

will run the development version of msui.

You can also use pixi's "run" subcommand to directly run a command in the development environment, like so::

    pixi run -e dev msui


Setup MSWMS server
------------------

In the MSS package is some demodata included. The default where this is stored is $HOME/mss. Your clone of the
MSS repository needs a different folder, e.g. workspace/MSS. Avoid to mix data and source.

:ref:`demodata <demodata>` is provided by executing::

   mswms_demodata --seed

To use this data add the mswms_settings.py in your python path::

   export PYTHONPATH=~/mss
   mswms


Setup MSColab server
--------------------

The MSColab server is built using the Flask rest framework which communicates with the PyQt5 frontend of MSS.
You can view the default configuration of MSColab in the file `mslib/mscolab/conf.py`.
If you want to change any values of the configuration, please take a look at the "Configuring Your MSColab Server"
section in :ref:`mscolab`

When using for the first time you need to initialise your database. Use the command :code:`mscolab db --init`
to initialise it. The default database is a sqlite3 database.
You can add some dummy data to your database by using the command :code:`mscolab db --seed`.
The content of the dummy data can be found in the file `mslib/mscolab/seed.py`.

To start your server use the command :code:`mscolab start`. This would start the MSColab server on port 8083.
Going to http://localhost:8083/status should now show "MSColab server". This means your server has started successfully.
Now you can use the MSS desktop application to connect to it using the MSColab window of the application.


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

Usually building the docs also includes creating the images and pages for the gallery feature.
This can be omitted by setting an environment variable ::

   export GALLERY=False


To build the html version of it, you need to have sphinx installed::

   cd docs/
   make html


Then point a web browser at docs/_build/html/index.html.

For heading hierarchy we use ::

  H1
  ==

  H2
  --

  H3
  ..

  H4
  ~~



Run Tests
---------

Considering that the software environment is set up using pixi, you can run the test suite using::

    pixi run -e dev pytest -n logical

To avoid getting a lot of opened windows from the test run you can either prepend :code:`QT_QPA_PLATFORM=offscreen` like so::

    QT_QPA_PLATFORM=offscreen pixi run -e dev pytest -n logical

or install xvfb from your distributions package manager and use :code:`xvfb-run` like so::

    xvfb-run pixi run -e dev pytest -n logical

Other options for pytest are possible to use,
you can e.g. set a higher verbosity using :code:`-v`,
leave out the :code:`-n` option to run the tests sequentially instead of in parallel,
or select a specific subset of tests to run using the :code:`-k` option.


Verify Code Style
.................

A flake8 only test is done with `flake8 mslib tests`.

Coverage
........

::

   $ pytest --cov mslib tests

This plugin produces a coverage report, example::

    ----------- coverage: platform linux, python 3.7.3-final-0 -----------
    Name                                     Stmts   Miss Branch BrPart  Cover
    --------------------------------------------------------------------------
    mslib/__init__.py                            2      0      0      0   100%
    mslib/msui/__init__.py                      23      0      0      0   100%
    mslib/msui/aircraft.py                      52      1      8      1    97%
    mslib/msui/constants.py                     12      2      4      2    75%
    mslib/msui/flighttrack.py                  383    117    141     16    66%


Profiling
.........

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



Writing Tests
-------------

Ideally every new feature or bug fix should be accompanied by tests
that make sure that the feature works as intended or that the bug is indeed fixed
(and won't turn up again in the future).
The best way to find out how to write such tests is by taking a look at the existing tests,
maybe finding one that is similar
and adapting it to the new test case.

MSS uses pytest as a test runner and therefore their `docs <https://docs.pytest.org/en/latest/contents.html>`_ are relevant here.

Common resources that a test might need,
like e.g. a running MSColab server or a QApplication instance for GUI tests,
are collected in :mod:`tests.fixtures` in the form of pytest fixtures that can be requested as needed in tests.

Keyring Features
-----------------

This document outlines step-by-step instructions for using the keyring features using the command line.

Prerequisites
..............

1. **Confirm the Default Keyring Backend**

   Use the following command to list available keyring backends and check which one is currently in use:

   .. code-block:: bash

       keyring --list-backends

Command-Line Commands for Keyring
..................................

1. **Set a Password**

   Store a password for a specific service and user:

   .. code-block:: bash

       keyring set SERVICE_NAME USERNAME

   **Example:**

  - Case 1: Standard Service Name
   .. code-block:: bash

       keyring set http://localhost:8083 myname@mydomain

  - Case 2: Custom Authentication Service
   .. code-block:: bash

       keyring set MSCOLAB_AUTH_http://localhost:8083 mscolab

  - The command will securely prompt you to input a password (e.g., `example_password`).

2. **Get a Password**

   Retrieve the stored password for a service and user:

   .. code-block:: bash

       keyring get SERVICE_NAME USERNAME

   **Example:**

   - Case 1: Standard Service Name
   .. code-block:: bash

       keyring get http://localhost:8083 myname@mydomain

   - Case 2: Custom Authentication Service
   .. code-block:: bash

       keyring get MSCOLAB_AUTH_http://localhost:8083 mscolab

   **Output:**

   .. code-block::

       example_password

3. **Delete a Password**

   Remove the stored password for a service and user:

   .. code-block:: bash

       keyring del SERVICE_NAME USERNAME

   **Example:**

  - Case 1: Standard Service Name
   .. code-block:: bash

       keyring del http://localhost:8083 myname@mydomain

  - Case 2: Custom Authentication Service
   .. code-block:: bash

       keyring del MSCOLAB_AUTH_http://localhost:8083 mscolab

   To confirm the deletion, attempt to retrieve the password:

   .. code-block:: bash

       keyring get MSCOLAB_AUTH_http://localhost:8083 mscolab


Changing the database model
---------------------------

Changing the database model requires adding a corresponding migration script to MSS,
so that existing databases can be migrated automatically.

To generate such a migration script you can run::

  flask --app mslib.mscolab.app db migrate -d mslib/mscolab/migrations -m "To version <next-major-version>"

Depending on the complexity of the changes that were made,
the generated migration script might need some tweaking.

If there is already a migration script for the next release,
then please incorporate the generated migration script into this existing one,
instead of adding a new one.
You can still generate a script with the above command first
to get a starting point for the changes.


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




Merging stable into develop
---------------------------

Bug fixes we have done in stable we need to merge regularly into develop too::

   git checkout stable
   git pull git@github.com:Open-MSS/MSS.git stable
   git checkout develop
   git pull git@github.com:Open-MSS/MSS.git develop
   git checkout -b merge_stable_to_develop
   git merge stable
   git push git@github.com:Open-MSS/MSS.git merge_stable_to_develop


Then create the proposed merge request. The merge request must *not* be squashed or rebased.
To allow the merging, the requirement for a linear-history must be disabled *temporarily*
for the develop branch and one needs to ensure that the merge request is accepted with a
regular merge with merge commit. Remove the merge_stable_to_develop branch if still present.


Creating a new release
----------------------

* make sure all issues for this milestone are closed or moved to the next milestone
* update CHANGES.rst, based on git log
* check version number of upcoming release in CHANGES.rst
* verify that version.py, MANIFEST.in and setup.py are complete
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
-------------------------

MSS takes part in `Google Summer of Code <https://summerofcode.withgoogle.com/>`_
as a `sub-organization of Python Software Foundation (PSF) <https://python-gsoc.org/>`_.


GSoC'24 Projects
................

- `Aryan Gupta: (MSS) msui: Improve MSUI : GSoC 2024 <https://github.com/Open-MSS/MSS/wiki/Aryan-Gupta:-(MSS)-msui:-Improve-MSUI-:-GSOC2024>`_
- `Preetam Sundar Das: MISSION SUPPORT SYSTEM(MSS): GUI FOR AUTOMATED PLOTTING : GSOC 2024 <https://github.com/Open-MSS/MSS/wiki/Preetam-Sundar-Das:-MISSION-SUPPORT-SYSTEM(MSS):-GUI-FOR-AUTOMATED-PLOTTING-:-GSOC2024>`_
- `Rohit Prasad: Mission Support System: Improve multiple flightpath docking widget : GSOC 2024 <https://github.com/Open-MSS/MSS/wiki/Rohit-Prasad:-Mission-Support-System:-Improve-multiple-flightpath-docking-widget-:-GSOC2024>`_


GSoC'23 Projects
................

- `Shubh Gaur: Mission Support System(MSS) : UI-improvements : GSOC 2023 <https://github.com/Open-MSS/MSS/wiki/UI%E2%80%90improvements-GSOC-2023>`_

- `Nilupul Manodya: Mission Support System : Implement a SAML 2.0 service provider (SP) into mscolab : GSOC 2023 <https://github.com/Open-MSS/MSS/wiki/Implement-a-SAML-2.0-service-provider-(SP)-into-mscolab-:-GSOC-2023>`_




GSoC'22 Projects
................

- `Sreelakshmi Jayarajan: Automated Command Line Plotting Tool : GSoC 2022 <https://github.com/Open-MSS/MSS/wiki/Automated-Command-Line-Plotting-Tool-:-GSoC-2022>`_

- `Jatin Jain: UI and server improvements GSOC 2022 <https://github.com/Open-MSS/MSS/wiki/UI-and-server-improvements-GSOC-2022>`_


GSoC'21 Projects
................

- `Hrithik Kumar Verma: Generating a tool chain tutorial for the MSUI user interface by automation operations : GSoC 2021 <https://github.com/Open-MSS/MSS/wiki/Generating-a-tool-chain-tutorial-for-the-MSUI-user-interface-by-automation-operations-:-GSoC---2021>`_

- `Aravind Murali: MSUI: UI Redesign GSOC 2021 <https://github.com/Open-MSS/MSS/wiki/MSUI:-UI-Redesign---GSOC-2021>`_


GSoC'20 Projects
................

- `Aryan Gupta: Mission Support System : Enhance KML Support <https://github.com/Open-MSS/MSS/wiki/KML:-Enhance-KML-Support---GSoC-2020>`_

- `Tanish Grover: Mission Support System: Mission Support Collaboration Improvements <https://github.com/Open-MSS/MSS/wiki/Mscolab:-Mission-Support-Collaboration-Improvements---GSoC-2020>`_

GSoC'19 Projects
................

- `Anveshan Lal: Updating Geographical Plotting Routines <https://github.com/Open-MSS/MSS/wiki/Cartopy:-Updating-Geographical-Plotting-Routines----GSoC-2019>`_

- `Shivashis Padhi: Collaborative editing of flight path in real-time <https://github.com/Open-MSS/MSS/wiki/Mscolab:-Collaborative-editing-of-flight-path-in-real-time---GSoC19>`_
