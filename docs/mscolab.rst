MSColab - A Flight Path Collaboration Platform
==============================================

Mscolab has been developed to make MSS workable in a collaborative environment, with additional features such as
chat-messages, keeping track of the made changes, permissions of the collaborators.

.. _mscolab:

Configuring Your MSColab Server
-------------------------------
The mscolab server comes with a default configuration, built on top of :code:`sqlite3`. One can override these settings by making a copy
of the following file in a location in :code:`$PYTHONPATH`.

Description of the variables can be found in comments.

**mscolab_settings.py**

 .. literalinclude:: samples/config/mscolab/mscolab_settings.py.sample

.. _configuration-mscolab:

Protecting Login
................
The login to the MSColab server can be protected by an additional auth method.

 .. literalinclude:: samples/config/mscolab/mscolab_auth.py.sample

Make a copy of the above file, rename it to mscolab_auth.py, make the necessary changes in the file and add it to your $PYTHONPATH.

Steps to Run MSColab Server
---------------------------
  - The MSColab server comes included in the MSS python package.
  - Once MSS is installed, if you're running the mscolab server for the first time, run the command :code:`mscolab db --init` to initialise your database.
  - To start the server run :code:`mscolab start`.
  - If you ever want to reset or add dummy data to your database you can use the commands :code:`mscolab db --reset` and :code:`mscolab db --seed` respectively.



Notes for server administrators
-------------------------------

If you're configuring mscolab server, there is a manage users GUI to add or manage users to a operation.
There is a command line tool available with the installation of mss, :code:`mscolab`. It can import users to the database
and can handle joins to operations.

Make a text file with the following format to import many users to the mscolab database

 .. code-block:: text

  suggested_username name <email>
  suggested_username2 name2 <email2>

 .. code-block:: text

  $ mscolab db --users_by_file /path/to/file

After executed you get information to exchange with users.

 .. code-block:: text

  Are you sure you want to add users to the database? (y/[n]):
  y
  Userdata: email suggested_username 30736d0350c9b886

  Userdata: email2 suggested_username2 342434de34904303


Further options can be listed by `mscolab db -h`

User Groups for Operations
..........................
When you want to use same set of users for different operations using same category
you can do this by setting up users in a special operation.

On a given category for an operation ending with GROUP_POSTFIX
e.g. on a category = Tex it will look for TexGroup.
All users in that TexGroup operation are set to all operations of that category
having same roles as in the TexGroup.

The default ::

    GROUP_POSTFIX = "Group"


User verification by email
..........................

With setting of `MAIL_ENABLED = True` you have to set further options in the mscolab_settings.py. These are
parameters of `flask-mail` ::

        # enable verification by Mail
        MAIL_ENABLED = True

        # mail settings
        MAIL_SERVER = 'localhost'
        MAIL_PORT = 25
        MAIL_USE_TLS = False
        MAIL_USE_SSL = True

        mail authentication
        MAIL_USERNAME = os.environ.get('APP_MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('APP_MAIL_PASSWORD')

        # mail accounts
        MAIL_DEFAULT_SENDER = 'MSS@localhost'

A new user gets an email with an url including a token to become verified on the mscolab server. After the verification
she can login.
If an existing user does not remember the password, she can reset the password by sending an email to the user's email
address and using the token that the system sent along with the email.

Instructions to use mscolab wsgi
................................

Create a file called :code:`server.py` having this line::

  from mslib.mscolab.server import _app as app

Then install gunicorn by pixi::

  $ pixi global install gunicorn


and start the server by::

  $ gunicorn -b 0.0.0.0:8087 server:app

For further options read `<https://flask.palletsoperations.com/en/1.1.x/deploying/wsgi-standalone/#gunicorn>`_

If you want to use nginx to proxy this gunicorn server have a look on the example
:download:`mss_proxy.conf <samples/nginx/sites-available/mss_proxy.conf>`.

.. tip:: update gunicorn

  You may need to build gunicorn on your own until the new release > 20.1.0:
  https://github.com/benoitc/gunicorn/pull/2581#issuecomment-1154008037

Backup Data Base
................

For backups you can dump by `pg_dump -d mscolab -f output.sql` the sqlite database
and restore it by `psql -v ON_ERROR_STOP=1 < new_db.sql`

On a PostgreSQL db you can regularly do backups by creating a dump
by `pg_dump <https://www.postgresql.org/docs/current/app-pgdump.html>`_ using a cron job ::

    #!/bin/bash
    timestamp=$(date +%Y%m%d_%H%M)
    pg_dump -d mscolab -f "/home/mscolab/dump/$timestamp.sql"


Database Migration from Version 8 or 9
.................................

From v10 onwards MSColab uses `Flask-Migrate <https://flask-migrate.readthedocs.io/en/latest/>` to automatically deal with database migrations.
To upgrade from v8 or v9 a recreation of the database and subsequent copy of existing data is necessary.
To do this follow these steps:

#. Stop MSColab completely, no process interacting with the MSColab database should remain running
#. **Make a backup of your existing database**
#. Set ``SQLALCHEMY_DB_URI_TO_MIGRATE_FROM`` to your existing database
#. Set ``SQLALCHEMY_DB_URI`` to a new database
#. If you are not using SQLite: create the new database
#. Start MSColab
#. Check that everything was migrated successfully
#. Unset ``SQLALCHEMY_DB_URI_TO_MIGRATE_FROM``

If you want to keep using your old database URI you can first rename your existing database so that it has a different URI
and just set ``SQLALCHEMY_DB_URI_TO_MIGRATE_FROM`` to that.


Steps to use the MSColab UI features
------------------------------------

To get access to the mscolab feature click Connect.


User based features
....................
  - A user can register and login.
  - A user can also delete his/her account.

Operation based features
........................

  - In MSColab, each flight track is referred to as an operation.
  - An operation can be created by a user, once he/she has logged in.
  - The users can either select a starting FTML file while creating the operation or can later import a FTML file to the operation.
  - All the operations the user has created or has been added to can be found in Mscolab's main window along with the user's access level.
  - To start working on an operation the user needs to select it which enables all the operation related buttons.
  - Any change made to an operation by a user will be shared with everyone in real-time unless `Work Locally` is turned on.(More on this later)
  - Operations can be manually archived to remove them from normal view without having to delete them.
    They can be found again in the Archive view, where they can be unarchived for further use.

Operation Permissions
.....................

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
..............................

To add users to a operation, you need to be the admin or creator of that operation. Select the desired operation and click on the `Manage Users` button in Mscolab's main window.
An admin window will open where you can manage the permission of all the users in bulk by selecting multiple users at once and add, updating or deleting their access to the operation.
If you have another operation and want to have the same users as on that operation you can use the `Clone Permissions` option in the admin window to quickly add all the users of a operation to your selected one.


Chatting With Operation Members
...............................

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
...........................

If you have the access level of collaborator or higher to a operation you can view all the change history of the operation by clicking on the `Version History` button in Mscolab's main window.
A new version history window will be opened where you can view all the changes made to the operation and compare them with the current flight track by selecting a previous version.
You can also set names to important versions to keep track of all the important milestones.


Working Locally on an Operation
...............................

If you want to try out your changes on a operation without disturbing the common shared file. You can use the `Work Locally` toggle in the Mscolab main window.
You can turn that toggle on at any time which would send you into local work mode. In this mode you will have a copy of the operation on your system and all your changes will be made to this file.
Once you're done with all your local work and think you're ready to push your changes to everyone, you can use the `Save to Server` button.
This would prompt you with a dialog where you can compare your local flight track and the common flight track on the server and select what you would like to keep.
You can also fetch the common flight track to your local file at any time using the `Fetch from Server` button which prompts you with a similar dialog.
You can turn the `Work Locally` toggle off at any points and work on the common shared file on the server. All your local changes are saved and you can return to them at any point by toggling the checkbox back on.
