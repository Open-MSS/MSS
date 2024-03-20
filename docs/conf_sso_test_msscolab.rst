Configuration MSS Colab Server with Testing IdP for SSO
=======================================================
Testing IDP (`mslib/msidp`) is specifically designed for testing the Single Sign-On (SSO) process with the mscolab server using PySAML2. This is solely for development and testing purposes, do not use in production environments.

Here is documentation that explains the configuration of the MSS Colab Server with the testing IdP.

Getting started
---------------

To set up a local identity provider with the mscolab server, you'll first need to generate the required keys and certificates for both the Identity Provider and the mscolab server. Follow these steps to configure the system:

    1. Initial Steps
    2. Generate Keys and Certificates
    3. Enable USE_SAML2
    4. Generate Metadata Files
    5. Start the Identity Provider
    6. Start the mscolab Server
    7. Test the Single Sign-On (SSO) Process


1. Initial Steps
----------------
Before getting started, you should correctly activate the environments, set the correct Python path as explained in the mss instructions : https://github.com/Open-MSS/MSS/tree/develop#readme



2. Generate Keys, Certificates, and backend_saml files
------------------------------------------------------

This involves generating both `.key` files and `.crt` files for both the Identity provider and mscolab server and `backend_saml.yaml` file. 

Before running the command make sure to set `USE_SAML2 = False` in your `mscolab_settings.py` file,  You can accomplish this by following these steps:

- Add to the `PYTHONPATH` where your `mscolab_settings.py`.
- Add `USE_SAML2 = False` in your `mscolab_settings.py` file.

.. note::
    If you set `USE_SAML2 = True` without keys and certificates, this will not execute. So, make sure to set `USE_SAML2 = False` before executing the command.

If everything is correctly set, you can generate keys and certificates simply by running

.. code:: text

    $ mscolab sso_conf --init_sso_crts

.. note::
    This process generating keys and certificates for both Identity provider and mscolab server by default, If you need configure with different keys and certificates for the Identity provider, You should manually update the path of `SERVER_CERT` with the path of the generated .crt file for Identity provider, and `SERVER_KEY` with the path of the generated .key file for the Identity provider in the file `MSS/mslib/idp/idp_conf.py`.


3. Enable USE_SAML2
-------------------

To enable SAML2-based login (identity provider-based login), 

- To start the process update `USE_SAML2 = True` in your `mscolab_settings.py` file.

.. note::
    After enabling the `USE_SAML2` option, the subsequent step involves adding the `CONFIGURED_IDPS` dictionary for the MSS Colab Server. This dictionary must contain keys for each active Identity Provider, denoted by their `idp_identity_name`, along with their respective `idp_name`. Once this dictionary is configured, it should be utilized to update several aspects of the mscolab server, including the SAML2Client configuration in the .yml file. This ensures seamless integration with the enabled IDPs. By default, configuration has been set up for the localhost IDP, and any additional configurations required should be performed by the developer.

4. Generate metadata files
--------------------------

This involves generating necessary metadata files for both the identity provider and the service provider. You can generate them by simply running the below command.

.. note::
    Before executing this, you should set `USE_SAML2=True` as described in the third step(Enable USE_SAML2).

.. code:: text

    $ mscolab sso_conf --init_sso_metadata


5. Start Identity provider
--------------------------

Once you set certificates and metada files you can start mscolab server and local identity provider. To start local identity provider, simply execute:

.. code:: text

    $ msidp


6. Start the mscolab Server
---------------------------

Before Starting the mscolab server, make sure to do necessary database migrations.

When this is the first time you setup a mscolab server, you have to initialize the database by:

.. code:: text

    $ mscolab db --init

.. note::
   An existing database maybe needs a migration, have a look for this on our documentation.

   https://mss.readthedocs.io/en/stable/mscolab.html#data-base-migration

When migrations finished, you can start mscolab server  using the following command:

.. code:: text

    $ mscolab start


7. Testing Single Sign-On (SSO) process
---------------------------------------

* Once you have successfully launched the server and identity provider, you can begin testing the Single Sign-On (SSO) process.
* Start MSS PyQt application:

.. code:: text

    $ msui

* Login with identity provider through Qt Client application.
* To log in to the mscolab server through the identity provider, you can use the credentials specified in the ``PASSWD`` section of the ``MSS/mslib/msidp/idp.py`` file. Look for the relevant section in the file to find the necessary login credentials.
