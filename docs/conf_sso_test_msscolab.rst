Configuration MSS Colab Server with Testing IDP for SSO
=======================================================
Testing IDP (`mslib/idp`) is designed specifically for testing the Single Sign-On (SSO) process using PySAML2.

Here is documentation that explains the configuration of the MSS Colab Server with the testing IDP.

Getting started
---------------

To set up a local identity provider with the mscolab server, you'll first need to generate the required keys and certificates for both the Identity Provider and the mscolab server. Follow these steps to configure the system:

    1. Initial Steps
    2. Generate Keys and Certificates
    3. Enable IDP Login
    4. Generate Metadata Files
    5. Start the Identity Provider
    6. Restart the mscolab Server
    7. Test the Single Sign-On (SSO) Process


Initial Steps
-------------
Before getting started, you should correctly activate the environments, set the correct Python path, and be in the correct directory (`$ cd MSS`), as explained in the mss instructions : https://open-mss.github.io/develop/Setup-Instructions



Generate Keys and Certificates
------------------------------

This involves generating both .key files and .crt files for both the Identity provider and mscolab server. You can create these simply by running

`$ python mslib/mscolab/mscolab.py sso_conf --init_sso_crts`

In some cases, if you set `IDP_ENABLED = True` without certificates, this will not execute. So, make sure to set `IDP_ENABLED = False` before executing this


Enable IDP login
----------------

To enable identity provider-based login, set `IDP_ENABLED = True` in the `mslib/mscolab/conf.py` file of the MSS Colab server.

After enabling the IDP, the next step is to add the `CONFIGURED_IDPS` dictionary. This dictionary should include keys for each enabled Identity Provider, represented by `idp_identity_name`, and their corresponding `idp_name`. Once this dictionary is set up, it should be used to update various functionalities of the mscolab server, such as the SAML2Client config .yml file, ensuring proper integration with the enabled IDPs.


Generate metadata files
-----------------------

This involves generating necessary metadata files for both the identity provider and the service provider. You can generate them by simply running the appropriate command.

Before executing this, you should enable IDP login as described in the third step(Enable IDP login).

`$ python mslib/mscolab/mscolab.py sso_conf --init_sso_metadata`


Start Identity provider
-----------------------

Once you setted certificates and metada files you can start mscolab server and local identity provider. To start local identity provider, simpy execute

`$ python mslib/idp/idp.py idp_conf`


Restart the mscolab Server
--------------------------

Start mscolab server

`$ python mslib/mscolab/mscolab.py start`


Testing Single Sign-On (SSO) process
------------------------------------

* Once you have successfully launched the server and identity provider, you can begin testing the Single Sign-On (SSO) process.
* Start MSS PyQT application `$ python mslib/msui/msui.py`.
* Login with identity provider through Qt Client application.
* To log in to the mscolab server through the identity provider, you can use the credentials specified in the ``PASSWD`` section of the ``MSS/mslib/idp/idp.py`` file. Look for the relevant section in the file to find the necessary login credentials.
