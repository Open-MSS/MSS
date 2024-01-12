SSO via SAML Integration Guide for MSColab Server
=================================================

In this documentation, you will go through the following topics.

    1. Introduction
    
    2. Configuring an existing IdP
    
        * Private key and certificate
        
        * Configuring MSColab settings
        
            * MSColab configurations
            * Establish pysaml2, Saml2Client for the MSColab server
            
        * Configuration `mss_saml2_backend.yaml` file
        
        * Access SAML2Client metadata of MSColab
        
        * Guide to IDP Configuration

    3. Configuration example through Keycloak 13.0.1
    
        * Setting Up Keycloak
        
            * Installation and run Keycloak
            * Setup Keycloak IdP
            
        * Configure MSColab server
        
            * Configuration in MSColab settings for Keycloak
            * Configuration `mss_saml2_backend.yaml` file

    4. Configuration Multiple IDPs

1. Introduction
***************
This documentation will explain how to configure MSColab with an existing IdP or multiple IdPs, along with examples of implementation.

If you are not aware of how the SAML process works in the MSColab server, it is highly recommended to set up msidp and test it with MSColab as an initial step before configuring existing 3rd party IdPs.

.. note::
    You can find instructions to set up msidp by `conf_sso_test_msscolab.rst`.


2. Configuring an existing IdP
******************************

To configure an existing IdP, you will need a signed certificate and a private key for the MSColab server. Additionally, you will require metadata for the IdP to complete the configuration.

Furthermore, you will need to configure saml2 setup in your `setup_saml2_backend.py` file and configure settings in your `mscolab_settings.py` file. On development you need only to use your PYTHONPATH and `setup_saml2_backend.py`, `mscolab_settings.py` in that path.

.. note::
    When you want to set a parameter or change a default add it to that file,
    
    eg:-

        $ more mscolab_settings.py
        
        use_saml2 = True

Also, you should be careful to return the attributes `username` and `email` address accordingly from the IdP along with the SAML response.

Private key and certificate
---------------------------

You can store your private key and certificate in any highly secure location. To configure MSColab for SSO, you just need to specify the paths to your certificate and key files in the configuration.

Private key and certificates path can be setup by your `mss_saml2_backend.yaml` file or when you Establishing Saml2Client for the MSColab server in your `setup_saml2_backend.py` file.


Configuring MSColab settings
----------------------------

MSColab configurations
######################

This section provides a guide for implementing MSColab with a single IdP. You can make the necessary changes in your `mscolab_settings.py` or `conf.py` file and your `setup_saml2_backend.py`.

.. note:: 
	Sensible defaults of MSColab are opinionated. All these are defined in conf.py and those which you want to change you can add to a mscolab_settings.py in your search path.

Before running the MSColab server, ensure `USE_SAML` is set to `True` in your `mscolab_settings.py`.

.. code:: text

	# enable login by identity provider
    	use_saml2 = True

To enabling login via the Identity Provider; need to implement `mss_saml2_backend.yaml` with paths for .crt and .key files, configure mscolab_settings.py, and configure `setup_saml2_backend.py`

In this implementation, as we are enabling only one IdP, there is no need to configure the default testing IdP (msidp). You can disable it simply by removing ``localhost_test_idp`` from the list of ``CONFIGURED_IDPS`` in your `setup_saml2_backend.py` file. Additionally, remember to add your ``idp_identity_name`` and ``idp_name`` accordingly.


.. code:: text

	# idp settings
    class setup_saml2_backend:
         CONFIGURED_IDPS = [
             {
                      'idp_identity_name': 'localhost_test_idp',  #  make sure to use underscore for the blanks
                      'idp_data': {
                          'idp_name': 'Testing Identity Provider',  #  this name is used on the Login page to connect to the Provider
                      }
                  },
          ,]


.. note::
    Please refer to the sample template `setup_saml2_backend.py.sample` located in the `docs/samples/config/mscolab` directory.

	Idp_identity_name refers to the specific name used to identify the particular Identity Provider within the MSColab server. This name should be used in the `mss_saml2_backend.yaml` file when configuring your IdP, as well as in the MSColab server configurations. It's important to note that this name is not visible to end users
    
    Remember to use underscore for the blanks in your `idp_identity_name`.

	Idp_name refers to the name of the Identity Provider that will be displayed in the MSColab server web interface for end users to select when configuring SSO.


Establish pysaml2, Saml2Client for the MSColab server
#####################################################

You should establish a Saml2Client, a component designed for handling SAML 2.0 authentication flows. This Saml2Client will be configured to work seamlessly with the MSColab server, ensuring that authentication requests and responses are handled correctly.

You should do implementation by your `setup_saml2_backend.py` file.

.. code:: text

    # if multiple 3rd party exists, development should need to implement accordingly below
    """
    	if 'idp_2'== configured_idp['idp_identity_name']:
    	# rest of code
    	# set CRTs and metadata paths for the idp_2
    	# configuration idp_2 Saml2Client
    """

After completing these steps, you can proceed to configure the `mss_saml2_backend.yaml` file.

Configuration mss_saml2_backend.yaml file
-----------------------------------------

You should create a new attribute using the ``idp_identity_name`` defined in the previous step. Afterward, you will need to create the necessary attributes in the `.yaml` file accordingly. If need, you can also update these attributes using the server

Please refer the yaml file template (`mss_saml2_backend.yaml.samlple`) in the directory of `docs/samples/config/mscolab` to generating your IdP file.

.. code:: text

   # SP Configuration for IDP 2
   sp_config_idp_2:
     name: "MSS Colab Server - Testing IDP(localhost)"
     description: "MSS Collaboration Server with Testing IDP(localhost)"
     key_file: mslib/mscolab/app/key_sp.key
     cert_file: mslib/mscolab/app/crt_sp.crt
     organization: {display_name: Open-MSS, name: Mission Support System, url: 'https://open-mss.github.io/about/'}
     
     contact_person:
     	- {contact_type: technical, email_address: technical@example.com, given_name: Technical}
     	- {contact_type: support, email_address: support@example.com, given_name: Support}
        
     metadata:
       local: [mslib/mscolab/app/idp.xml]
     entityid: http://localhost:5000/proxy_saml2_backend.xml
     accepted_time_diff: 60
     service:
       sp:
         ui_info:
           display_name:
             - lang: en
               text: "Open MSS"
           description:
             - lang: en
               text: "Mission Support System"
           information_url:
             - lang: en
               text: "https://open-mss.github.io/about/"
           privacy_statement_url:
             - lang: en
               text: "https://open-mss.github.io/about/"
           keywords:
             - lang: en
               text: ["MSS"]
             - lang: en
               text: ["OpenMSS"]
           logo:
             text: "https://open-mss.github.io/assets/logo.png"
             width: "100"
             height: "100"
         authn_requests_signed: true
         want_response_signed: true
         want_assertion_signed: true
         allow_unknown_attributes: true
         allow_unsolicited: true
         endpoints:
           assertion_consumer_service:
             - [http://localhost:8083/idp2/acs/post, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST']
             - [http://localhost:8083/idp2/acs/redirect, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']
           discovery_response:
           - [<base_url>/<name>/disco, 'urn:oasis:names:tc:SAML:profiles:SSO:idp-discovery-protocol']
         name_id_format: 'urn:oasis:names:tc:SAML:2.0:nameid-format:transient'
         name_id_format_allow_create: true

.. note::
    Make sure to update 
    entityid : 'idp_identity_name' 
    Assertion_consumer_service : with the urls of assertion consumer services functionalities URL that going to implement next step, may be better to explain here

    Key_file : if need can be update through the server
    Cert_file : if need can be update through the server 
    Metadata.local : if need can be update through the server


Access SAML2Client metadata of MSColab
--------------------------------------

While the core purpose of IdPs is to authenticate users and provide information to relying parties, the responses can vary based on configuration, protocol, user attributes, consent, and customization. Therefore, responses from different IdPs can indeed be different, and developers and administrators should be aware of these variations when integrating with different identity providers. However, in the MSColab server, we implemented an easy way to access metadata from an endpoint. You can access it easily by using the specified url, which is configured based on the settings of your SAML2 client in your `setupsaml2backend.py` and `saml2backend.yaml` file. This streamlined approach simplifies the process and eliminates the need for manual development of endpoints and functionalities specific to each IdP.

.. note::
    URL to access metadata endpoint for particular IdP:
    ``/metadata/<idp_identity_name>``

Guide to IDP Configuration
--------------------------

In the SSO process through the MSColab server, the username is obtained as ``givenName``, and the email address is obtained as ``email``. Therefore, when configuring the IdP, it is necessary to configure it accordingly to ensure the correct return of the givenName attribute and the email address along with the SAML response.


3. Configuration example through Keycloak 13.0.1
************************************************

Setting Up Keycloak
-------------------

Installation and run Keycloak
#############################

Via local installation
    1. Download the file (requires java, wget installed):

    .. code:: text

        cd $HOME && \ wget -c keycloak_13_0_1.tar.gz https://github.com/keycloak/keycloak/releases/download/13.0.1/keycloak-13.0.1.tar.gz -O - | tar -xz

|

    2. Navigate to the KeyCloak binaries folder:

    .. code:: text

        cd keycloak-13.0.1/bin

|

    3. And start it up:

    .. code:: text

        ./standalone.sh

|

Via Docker (requires Docker installed)

    .. note::

        You can define KEYCLOAK_USER and KEYCLOAK_PASSWORD as you wish. Recommends using tools like pwgen to generate strong and random passwords.
    
    * Open your terminal and run

    .. code:: text

        docker run -p 8080:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=pwgen_password quay.io/keycloak/keycloak:13.0.1

|

    .. image:: images/sso_via_saml_conf/ss_docker_run_cmd.png
        :width: 400



Setup Keycloak IdP
##################

Access Keycloak
    Once you successfully install and start keycloak, you can Access keycloak interface through a particular port using your web browser.
        eg:-  http://localhost:8080

        .. image:: images/sso_via_saml_conf/ss_interface_keycloak.png
            :width: 800

Login as an admin
    You can go to the admin console and  login as an admin by providing the above provided credentials.
    
        .. image:: images/sso_via_saml_conf/ss_admin_login.png
            :width: 400

Create realm
    Once successfully logged in you should create a realm to configure IdP. You can create a realm by clicking `Add realm` button.

        .. image:: images/sso_via_saml_conf/ss_add_realam_btn.png
            :width: 300

    You need to provide a name for your realm and create.

        .. image:: images/sso_via_saml_conf/ss_add_realam_name.png
            :width: 800

Create a client specifically for SAML

    Once you successfully created a realm, lets create a client specifically for SAML.

    First you should navigate into the client section using your left navigation.

        .. image:: images/sso_via_saml_conf/ss_left_nav_client.png
            :width: 200
    
    In the client section you can see `create` button in the top right corner.

    Create a new client by clicking `create` button in the top right corner.

        .. image:: images/sso_via_saml_conf/ss_create_client_btn.png
            :width: 800

        .. note::
            When creating client ID, it should be same as the issuer ID of the MSColab server.
            In here, the MSColab server used different issuer IDs for the particular idp_iedentity_name, and issued it by url bellow
	            
                http://127.0.0.1:8083/metadata/idp_identityname/


    Also make sure to select Client Protocol as saml.
        .. image:: images/sso_via_saml_conf/ss_set_client_protocol.png
                :width: 800

    After creating a SAML client, make sure you set Valid Redirect URIs to match our Service Provider.

        Eg:-
            http://127.0.0.1:8083/*
            
            http://localhost:8083/*

    
    Generate keys and certificates

        To generate keys and certificates first navigate into saml keys tab and click `Generate new keys` button.
            .. image:: images/sso_via_saml_conf/ss_gen_keys_crts.png
                :width: 800
        
        You can copy generated keys and certificates by clicking top of the key and certificate. After clicked you should need to create .crt and .key file accordingly.

        .. note::
            In here when you creating .key and .crt make sure to begin creating file structure accordingly.

                Eg:-	
                    .key file

                    ----BEGIN RSA PRIVATE KEY-----

                    Key key key key key key key
                    
                    -----END RSA PRIVATE KEY-----

                |

                    .crt file

                    -----BEGIN CERTIFICATE-----

                    Crt crt crt crt

                    -----END CERTIFICATE-----


    Configure keycloak IdP for endusers

        You can enable user registration through enabling, Realm Settings>login>User-registration

        First go to Realm settings through left navigation,

            .. image:: images/sso_via_saml_conf/ss_left_nav_realm_settings.png
                :width: 200

        Then goto `Login` tab and enable User registration.

            .. image:: images/sso_via_saml_conf/ss_enable_usr_reg.png
                :width: 800

    Add email and givenName into mappers

        .. note::
            In the MSColab server, we take the attribute name for email as `email` and for the username as `givenName`. Therefore, we need to implement mappers accordingly for the Keycloak end.

        In this example, We need to add the Keycloak built-in email mapper and givenName mapper to obtain it in our MSColab server through the SAML response with correct attribute names.

        eg:-

            clients>yourcreatedCliet>Mappers>Add Builtin Protocol Mapper enable email
        
        First navigate into client section through left navigation.

            .. image:: images/sso_via_saml_conf/ss_left_nav_client.png
                    :width: 200

        Select client we created already

            .. image:: images/sso_via_saml_conf/ss_client_select.png
                    :width: 800

        Go to the Mapper section tab, and Click `Add Builtin` button to add Mappers.

            .. image:: images/sso_via_saml_conf/ss_add_mappers_btn.png
                    :width: 800

        Since we need email address and givenName, enable those and click `add selected` button.

            .. image:: images/sso_via_saml_conf/ss_enable_mappers.png
                    :width: 800

        Then you can see Added mappers in your interface 

            .. image:: images/sso_via_saml_conf/ss_view_mappers.png
                    :width: 800


        Set SAML Attribute Names as `email` and `givenName`.

            .. image:: images/sso_via_saml_conf/ss_set_attribute_name1.png
                    :width: 800

            .. image:: images/sso_via_saml_conf/ss_set_attribute_name2.png
                    :width: 800

    Export IdP metadata

        When all sorted you need to export metadata file from the keycloak,

        http://localhost:8080/auth/realms/saml-example-realm/protocol/saml/descripto

        Since we're going to import the file with the name as "key_cloak_v_13_idp.xml" in this example, We should store it with the same name.


Configure MSColab server
########################

Configuration in MSColab settings for Keycloak
    This involves Updating your `conf.py` file or `mcolab_settigns.py`, and update your `conf.py` file or `setup_saml2_backend.py`.

    1. Set USE_SAML = True in your mcolab_settigns.py

        .. code:: text

            # enable login by identity provider
            use_saml2 = True

    2. Insert Keycloak into list of CONFIGURE_IDP in your setup_saml2_backend.py

        .. code:: text

            # idp settings
            class setup_saml2_backend:
                CONFIGURED_IDPS = [
                    {
                            'idp_identity_name': 'key_cloak_v_13',  #  make sure to use underscore for the blanks
                            'idp_data': {
                                'idp_name': 'Keycloak V 13',  #  this name is used on the Login page to connect to the Provider
                            }
                        },
                ,]

        .. note::
            Make sure to insert idp_identity_name as above ('key_cloak_v_13'), which used in this example.

Configuration mss_saml2_backend.yaml file

    Create your mss_saml2_backend.yaml file in your ``MSCOLAB_SSO_DIR``.

        .. code:: text

            name: Saml2
            config:
            entityid_endpoint: true
            mirror_force_authn: no
            memorize_idp: no
            use_memorized_idp_when_force_authn: no
            send_requester_id: no
            enable_metadata_reload: no


            # SP Configuration for localhost_test_idp
            key_cloak_v_13:
            name: "Keycloak Testing IDP"
            description: "Keycloak 13.0.1"
            key_file: path/to/key_sp.key # Will be set from the mscolab server
            cert_file: path/to/crt_sp.crt # Will be set from the mscolab server
            organization: {display_name: Open-MSS, name: Mission Support System, url: 'https://open-mss.github.io/about/'}
            contact_person:
            - {contact_type: technical, email_address: technical@example.com, given_name: Technical}
            - {contact_type: support, email_address: support@example.com, given_name: Support}


            metadata:
                local: [path/to/idp.xml] # Will be set from the mscolab server


            entityid: http://127.0.0.1:8083/metadata_keycloak/
            accepted_time_diff: 60
            service:
                sp:
                ui_info:
                    display_name:
                    - lang: en
                        text: "Open MSS"
                    description:
                    - lang: en
                        text: "Mission Support System"
                    information_url:
                    - lang: en
                        text: "https://open-mss.github.io/about/"
                    privacy_statement_url:
                    - lang: en
                        text: "https://open-mss.github.io/about/"
                    keywords:
                    - lang: en
                        text: ["MSS"]
                    - lang: en
                        text: ["OpenMSS"]
                    logo:
                    text: "https://open-mss.github.io/assets/logo.png"
                    width: "100"
                    height: "100"
                authn_requests_signed: true
                want_response_signed: true
                want_assertion_signed: true
                allow_unknown_attributes: true
                allow_unsolicited: true
                endpoints:
                    assertion_consumer_service:
                    - [http://localhost:8083/keycloak_idp/acs/post, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST']
                    discovery_response:
                    - [<base_url>/<name>/disco, 'urn:oasis:names:tc:SAML:profiles:SSO:idp-discovery-protocol']
                name_id_format: 'urn:oasis:names:tc:SAML:2.0:nameid-format:transient'
                name_id_format_allow_create: true


        .. note::
            make sure to set same issuer ID in your saml_2.yaml file correctly
                eg:- entityid: http://127.0.0.1:8083/metadata/

        .. note::
            may be can be occured invalid redirect url problem, since we defined localhost in keycloak admin, and using 127.0..... be careful to set it correctly.

            eg:- 
                assertion_consumer_service:
                        - [http://localhost:8083/localhost_test_idp/acs/post, 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST']
                        - [http://localhost:8083/localhost_test_idp/acs/redirect,]


4. Configuration Multiple IDPs
******************************

As we have already implemented one IdP, we can extend the list of IdPs and implement functions specific to each IdP as needed.
