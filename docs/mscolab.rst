Mscolab - A Flight Path Collaboration Tool
==========================================

Mscolab has been developed to make mss workable in a collaborative environment, with additional features such as
chat-messages, keeping track of the made changes, permissions of the collaborators.

.. _mscolab:

Configuring Your Mscolab Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The mscolab server comes with a default configuration, built on top of :code:`sqlite3`. One can override these settings by making a copy
of the following file in a location in :code:`$PYTHONPATH`.

Description of the variables can be found in comments.

**mscolab_settings.py**

 .. literalinclude:: samples/config/mscolab/mscolab_settings.py.sample

.. _configuration-mscolab:

Protecting Login
~~~~~~~~~~~~~~~~
The login to the mscolab server can be protected by an additional auth method.

**mss_mscolab_auth.py**

 .. literalinclude:: samples/config/mscolab/mss_mscolab_auth.py.sample

Steps to Run Mscolab Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~
  - The mscolab server comes included in the MSS python package.
  - Once mss is installed, if you're running the mscolab server for the first time, run the command :code:`mscolab db --init` to initialise your database.
  - To start the server run :code:`mscolab start`.
  - If you ever want to reset or add dummy data to your database you can use the commands :code:`mscolab db --reset` and :code:`mscolab db --seed` respectively.


Steps to Open the Mscolab Application Window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  - To open the mscolab window in the application select the `mscolab` option from the menu bar of Mission Support System's main window.
  - Mscolab UI will be in the future, the new main UI. For now, to get also users experience included we add it as a new menu in the tool-bar. We evolve the new UI by these inputs of more users and will deprecate in this process the old one.


User based features
~~~~~~~~~~~~~~~~~~~
  - A user can register and login.
  - A user can also delete his/her account.

Project based features
~~~~~~~~~~~~~~~~~~~~~~
  - In Mscolab, each flight track is referred to as a project.
  - A project can be created by a user, once he/she has logged in.
  - The users can either select a starting FTML file while creating the project or can later import a FTML file to the project.
  - All the projects the user has created or has been added to can be found in Mscolab's main window along with the user's access level.
  - To start working on a project the user needs to select it which enables all the project related buttons.
  - Any change made to a project by a user will be shared with everyone in real-time unless `Work Locally` is turned on.(More on this later)

Project Permissions
~~~~~~~~~~~~~~~~~~~~
There are 4 different access levels of user:


  - **Creator**

    Creator is the user who creates the project, they have all the rights which ‘admins’ have.
    Additionally, they can delete the project, make administrators and revoke administrators’ status.
  - **Admins**

    Admins can add users to the project and can update their access levels. They can also view the version history of the project and revert to a previous version if need arises.
    They have all the capabilities of a collaborator.
  - **Collaborators**

    Collaborators can make changes to the project and have access to the chat room. Additionally, they can view the version history of the project.
  - **Viewer**

    Viewers can only view the flight track and have the least amount of access.

All the changes to users’ permission are in real-time.


Adding Users To Your Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add users to a project, you need to be the admin or creator of that project. Select the desired project and click on the `Manage Users` button in Mscolab's main window.
An admin window will open where you can manage the permission of all the users in bulk by selecting multiple users at once and add, updating or deleting their access to the project.
If you have another project and want to have the same users as on that project you can use the `Clone Permissions` option in the admin window to quickly add all the users of a project to your selected one.


Chatting With Project Members
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If a user has the permission of collaborator or above, they can use the chat window in Mscolab. You can send normal text messages or use markdown to format them.
The currently supported markdown syntax is:

- # : Headings
- \*\*text\*\* : Bold text
- \*text\* : Italicise Text
- [text](link) : Add hyper-link to text

You can use the `Preview` button to see how your text is formatted before sending it.

There is also support for image/document upload. You can set the upload size limit in the mscolab_settings.py file. The default limit is 2 MBs.

Right-clicking on a message would open a context-menu giving you options to copy, edit, delete or reply to a message.


Managing Project Versions
~~~~~~~~~~~~~~~~~~~~~~~~~
If you have the access level of collaborator or higher to a project you can view all the change history of the project by clicking on the `Version History` button in Mscolab's main window.
A new version history window will be opened where you can view all the changes made to the project and compare them with the current flight track by selecting a previous version.
You can also set names to important versions to keep track of all the important milestones.


Working Locally on a Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you want to try out your changes on a project without disturbing the common shared file. You can use the `Work Locally` toggle in the Mscolab main window.
You can turn that toggle on at any time which would send you into local work mode. In this mode you will have a copy of the project on your system and all your changes will be made to this file.
Once you're done with all your local work and think you're ready to push your changes to everyone, you can use the `Save to Server` button.
This would prompt you with a dialog where you can compare your local flight track and the common flight track on the server and select what you would like to keep.
You can also fetch the common flight track to your local file at any time using the `Fetch from Server` button which prompts you with a similar dialog.
You can turn the `Work Locally` toggle off at any points and work on the common shared file on the server. All your local changes are saved and you can return to them at any point by toggling the checkbox back on.


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

  $ mamba install gunicorn eventlet
  $ gunicorn -b 0.0.0.0:8087 server:app
