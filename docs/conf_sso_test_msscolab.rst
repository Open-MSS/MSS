Configuration MSS Colab Server with Testing IDP for SSO
=======================================================
Testing IDP (`mslib/idp`) is designed specifically for testing the Single Sign-On (SSO) process using PySAML2.

Here is documentation that explains the configuration of the MSS Colab Server with the testing IDP.

Getting started
---------------


Enable IDP login
----------------

To enable identity provider-based login, set `IDP_ENABLED = True` in the `mslib/mscolab/conf.py` file of the MSS Colab server.

After enabling the IDP, the next step is to add the `CONFIGURED_IDPS` dictionary. This dictionary should include keys for each enabled Identity Provider, represented by `idp_identity_name`, and their corresponding `idp_name`. Once this dictionary is set up, it should be used to update various functionalities of the mscolab server, such as the SAML2Client config .yml file, ensuring proper integration with the enabled IDPs.


TLS Setup
---------

**Setting Up Certificates for Local Development**


To set up the certificates for local development, follow these steps:

1. Generate a primary key `(.key)` and a certificate `(.crt)` files using any certificate authority tool. You will need one for the MSS Colab server and another one for the identity provider. Make sure to name certificate of identity provider as `crt_idp.crt` and key as `key_idp.key`. Also name the certificate of msss colab server as `crt_sp.crt` and key as the `key_sp.key`.

    Here's how you can generate self-signed certificates and private keys using OpenSSL:
    
    * Generate a self-signed certificate and private key for the MSS Colab server
    
        ``openssl req -newkey rsa:4096 -keyout key_sp.key -nodes -x509 -days 365 -out crt_sp.crt``
    
    * Generate a self-signed certificate and private key for the Identity Provider (IdP)
    
        ``openssl req -newkey rsa:4096 -keyout key_idp.key -nodes -x509 -days 365 -out crt_idp.crt``

2. Copy and paste the certificate and private key into the following file directories:

    - Key and certificate of MSS Colab Server: ``MSS/mslib/mscolab/app/``

    - key and certificate of Identity Provider: ``MSS/mslib/idp/``

    Make sure to insert the key along with its corresponding certificate.

Configuring the MSS Colab server and Identity Provider
------------------------------------------------------

First, generate the metadata file (https://pysaml2.readthedocs.io/en/latest/howto/config.html#metadata) for the MSS Colab server. To do that, start the Flask application and download the metadata file by following these steps:

1. Navigate to the home directory, ``/MSS/``.
2. Start the MSS Colab Server by running ``$ python mslib/mscolab/mscolab.py start`` The application will listen on port : 8083.
3. Download the metadata file by executing the command: ``curl http://localhost:8083/metadata/ -o sp.xml``.
4. Move generated ``sp.xml`` to dir ``MSS/mslib/idp/``.

After that, generate the idp.xml file, copy it over to the Service Provider (SP), and restart MSS Coalb Server:

5. Go to the directory ``MSS/``.
6. Run the command
    ``$ make_metadata mslib/idp/idp_conf.py > mslib/mscolab/app/idp.xml``

    This executes the make_metadata tool from pysaml2, then saved XML content to the specified output file in the service provider dir: ``mslib/mscolab/app/idp.xml``.


Running the Application After Configuration
-------------------------------------------

Once you have successfully configured the MSS Colab Server and the Identity Provider, you don't need to follow the above instructions again. To start the application after the initial configuration, follow these steps:

1. Since here we changing Database modeling you need to make necessary Database migrations before running the mscolab server.

2. Start the MSS Colab server:

 * Navigate to the directory ``MSS/`` and run

    ``$ python mslib/mscolab/mscolab.py start``

3. Start the Identity Provider:

 * Navigate to the directory ``MSS/`` and run

    ``$ python mslib/idp/idp.py idp_conf``

By following the provided instructions, you will be able to set up and configure both the Identity Provider and MSS colab server for testing the SSO process.

Testing Single Sign-On (SSO) process
------------------------------------

* Once you have successfully launched the server and identity provider, you can begin testing the Single Sign-On (SSO) process.
* Start MSS PyQT application `$ python mslib/msui/msui.py`.
* Login with identity provider through Qt Client application.
* To log in to the mscolab server through the identity provider, you can use the credentials specified in the ``PASSWD`` section of the ``MSS/mslib/idp/idp.py`` file. Look for the relevant section in the file to find the necessary login credentials.
