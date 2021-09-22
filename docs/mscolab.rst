MSColab - A Flight Path Collaboration Platform
==============================================

Mscolab has been developed to make MSS workable in a collaborative environment, with additional features such as
chat-messages, keeping track of the made changes, permissions of the collaborators.

.. _mscolab:

Configuring Your MSColab Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The mscolab server comes with a default configuration, built on top of :code:`sqlite3`. One can override these settings by making a copy
of the following file in a location in :code:`$PYTHONPATH`.

Description of the variables can be found in comments.

**mscolab_settings.py**

 .. literalinclude:: samples/config/mscolab/mscolab_settings.py.sample

.. _configuration-mscolab:

Protecting Login
~~~~~~~~~~~~~~~~
The login to the MSColab server can be protected by an additional auth method.

**mss_mscolab_auth.py**

 .. literalinclude:: samples/config/mscolab/mss_mscolab_auth.py.sample

Steps to Run MSColab Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~
  - The MSColab server comes included in the MSS python package.
  - Once MSS is installed, if you're running the mscolab server for the first time, run the command :code:`mscolab db --init` to initialise your database.
  - To start the server run :code:`mscolab start`.
  - If you ever want to reset or add dummy data to your database you can use the commands :code:`mscolab db --reset` and :code:`mscolab db --seed` respectively.


Steps to Open the MSColab Application Window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  To open the mscolab window in the application select the `Operation` option from the menu bar of Mission Support System's main window.


User based features
~~~~~~~~~~~~~~~~~~~
  - A user can register and login.
  - A user can also delete his/her account.

Operation based features
~~~~~~~~~~~~~~~~~~~~~~
  - In MSColab, each flight track is referred to as an operation.
  - An operation can be created by a user, once he/she has logged in.
  - The users can either select a starting FTML file while creating the operation or can later import a FTML file to the operation.
  - All the operations the user has created or has been added to can be found in Mscolab's main window along with the user's access level.
  - To start working on an operation the user needs to select it which enables all the operation related buttons.
  - Any change made to an operation by a user will be shared with everyone in real-time unless `Work Locally` is turned on.(More on this later)

Operation Permissions
~~~~~~~~~~~~~~~~~~~~
There are 4 different access levels of user:


  - **Creator**

    Creator is the user who creates the operation, they have all the rights which ‘admins’ have.
    Additionally, they can delete the operation, make administrators and revoke administrators’ status.

  - **Admins**

    Admins can add users to the operation and can update their access levels. They can also view the version history of the operation and revert to a previous version if need arises.
    They have all the capabilities of a collaborator.

  - **Collaborators**

    Collaborators can make changes to the operation and have access to the chat room. Additionally, they can view the version history of the operation.

  - **Viewer**

    Viewers can only view the flight track and have the least amount of access.

All the changes to users’ permission are in real-time.


Adding Users To Your Operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add users to a operation, you need to be the admin or creator of that operation. Select the desired operation and click on the `Manage Users` button in Mscolab's main window.
An admin window will open where you can manage the permission of all the users in bulk by selecting multiple users at once and add, updating or deleting their access to the operation.
If you have another operation and want to have the same users as on that operation you can use the `Clone Permissions` option in the admin window to quickly add all the users of a operation to your selected one.


Chatting With Operation Members
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


Managing Operation Versions
~~~~~~~~~~~~~~~~~~~~~~~~~
If you have the access level of collaborator or higher to a operation you can view all the change history of the operation by clicking on the `Version History` button in Mscolab's main window.
A new version history window will be opened where you can view all the changes made to the operation and compare them with the current flight track by selecting a previous version.
You can also set names to important versions to keep track of all the important milestones.


Working Locally on an Operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you want to try out your changes on a operation without disturbing the common shared file. You can use the `Work Locally` toggle in the Mscolab main window.
You can turn that toggle on at any time which would send you into local work mode. In this mode you will have a copy of the operation on your system and all your changes will be made to this file.
Once you're done with all your local work and think you're ready to push your changes to everyone, you can use the `Save to Server` button.
This would prompt you with a dialog where you can compare your local flight track and the common flight track on the server and select what you would like to keep.
You can also fetch the common flight track to your local file at any time using the `Fetch from Server` button which prompts you with a similar dialog.
You can turn the `Work Locally` toggle off at any points and work on the common shared file on the server. All your local changes are saved and you can return to them at any point by toggling the checkbox back on.


Notes for server administrators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you're configuring mscolab server, there is a manage users GUI to add or manage users to a operation.
There is a command line tool available with the installation of mss, :code:`mscolab`. It can import users to the database
and can handle joins to operations.

Make a text file with the following format to import many users to the mscolab database

 .. code-block:: text

  suggested_username name <email>
  suggested_username2 name2 <email2>

 .. code-block:: text

  $ mscolab db --users_by_file /path/to/file

After executed you get informations to exchange with users.

 .. code-block:: text

  Are you sure you want to add users to the database? (y/[n]):
  y
  Userdata: email suggested_username 30736d0350c9b886

  "MSCOLAB_mailid": "email",
  "MSCOLAB_password": "30736d0350c9b886",


  Userdata: email2 suggested_username2 342434de34904303

  "MSCOLAB_mailid": "email2",
  "MSCOLAB_password": "342434de34904303",

Further options can be listed by `mscolab db -h`


Instructions to use mscolab wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

make a file called :code:`server.py`
and install ::

   mamba install eventlet==0.30.2 gunicorn

**server.py**::

  from mslib.mscolab.server import _app as app

Then run the following commands. ::

  $ mamba install gunicorn eventlet==0.30.2
  $ gunicorn -b 0.0.0.0:8087 server:app


For further options read `<https://flask.palletsoperations.com/en/1.1.x/deploying/wsgi-standalone/#gunicorn>`_