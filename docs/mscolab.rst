mscolab - Collaboration on Flighpathes
=======================================

Mscolab has been developed to make mss workable in a collaborative environment, with additional features such as
chat-messages, keeping track of the made changes, permissions of the collaborators.


Steps to run 
~~~~~~~~~~~~~~~~
  - Mscolab server has to be manually installed, the instructions can be found at :ref:`development`
  - Once mss is installed, mscolab server can be started by the command :code:`mscolab`
  - Mscolab UI will be in the future, the new main UI. For now, to get also users experience included we add it as a new menu in the tool-bar. We evolve the new UI  by these inputs of more users and will deprecate in this process the old one.
  - To start mscolab from ui select `mscolab` option in msui menu.

.. _configuration-mscolab:

Configuration of mscolab
~~~~~~~~~~~~~~~~~~~~~~~~
The mscolab server comes with a default configuration, built on top of :code:`sqlite3`. One can override these settings by making a copy
of the following file in a location in :code:`$PYTHONPATH`.

Description of the variables can be found in comments.

**mscolab_settings.py**

 .. literalinclude:: samples/config/mscolab/mscolab_settings.py.sample


User based features
~~~~~~~~~~~~~~~~~~~
  - User can register, login.

Project based features
~~~~~~~~~~~~~~~~~~~~~~
  - Once logged in, project can be created.
  - The project list can be found in mscolab’s main window, along with permissions
  - One has to activate the project, and options to open view windows/project window would show.( Project window has options to chat, checkout to an older change, add or remove collaborators)
  - While creating a project, once can select a file to work with.

Permission based features
~~~~~~~~~~~~~~~~~~~~~~~~~
There are 4 categories of user.


  - **Creator**

    Creator is a user who creates the project, they have all the rights which ‘admins’ have. Additionally, they can make administrators and revoke administrators’ status.
  - **Admins**

    Administrators can enable autosave(more on this later in this documentation). 
    They can change categories of collaborators and viewers. They have all the capabilities of a collaborator.
  - **Collaborators**

    They can chat in the room, and make changes to the collaborative project.
  - **Viewer**

    They can only view the changes in waypoints and chat in a room.

All the changes to users’ permission are realtime.

Notes regarding current release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  - Autosave mode has to be enabled at this stage. Only admins/creators can enable autosave. If enabled, all the changes are synced across all instances of mscolab opened by users. Else there’d be conflicted files.
  - However, all the changes are stored as VCS commits, so the project can be reverted to any past state safely.

Notes for server administrators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you're configuring mscolab server, there isn't a GUI to add or manage a group of users. There is however a
proposal to bring this on around the next release of mss. For now, there is a command line tool available with the
installation of mss, :code:`mscolab_add_permissions`. It's usage is as follows

- Make a text file with the following format

 .. code-block:: text

  path1
    u1-c
    u2-c
    u3-a

    path2
    u1-a

    path3
    u2-v

- `path1` represents the path of project in mscolab db. 
- u1, u2, u3 are usernames. 
- `c` stands for collaborator, `a` for admin, `v` for viewer.
- Different paths are separated by 2 '\n's.
- The tool can be invocated anywhere by a command, where :code:`/path/to/file` represents the path to file created above.

 .. code-block:: text

  $ mscolab_add_permissions /path/to/file

instructions to use mscolab wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make a file called :code:`server.py`

**server.py**::

  from mslib.mscolab.server import _app as app

Then run the following commands. ::

  $ conda install gunicorn eventlet
  $ gunicorn -b 0.0.0.0:8087 server:app
