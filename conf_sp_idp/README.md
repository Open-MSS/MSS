# Identity Provider and Service Provider for testing the SSO process

The `conf_sp_idp` designed for testing the Single Sign-On (SSO) process using PySAML2. This folder contains both the Identity Provider (IdP) and Service Provider (SP) implementations.

The Identity Provider was set up following the official documentation of [PySAML2](https://pysaml2.readthedocs.io/en/latest/), along with examples provided in the repository. Metadata YAML files will generate using the built-in tools of PySAML2. Actual key and certificate files can be used in when actual implementation. Please note that this project is intended for testing purposes only.

## Getting started

### TLS Setup

**Setting Up Certificates for Local Development**


To set up the certificates for local development, follow these steps:

1. Generate a primary key `(.key)` and a certificate `(.crt)` files using any certificate authority tool. You will need one for the service provider and another one for the identity provider. Make sure to name certificate of identity provider as `crt_idp.crt` and key as `key_idp.key`. Also name the certificate of service provider as `crt_sp.crt` and key as the `key_sp.key`.

Here's how you can generate self-signed certificates and private keys using OpenSSL:
* Generate a self-signed certificate and private key for the Service Provider (SP)
    ```
    openssl req -newkey rsa:4096 -keyout key_sp.key -nodes -x509 -days 365 -out crt_sp.crt
    ```
* Generate a self-signed certificate and private key for the Identity Provider (IdP)
    ```
    openssl req -newkey rsa:4096 -keyout key_idp.key -nodes -x509 -days 365 -out crt_idp.crt
    ```

2. Copy and paste the certificate and private key into the following file directories:
    * Key and certificate of Service Provider: `MSS/conf_sp_idp/sp/`
    * key and certificate of Identity Provider: `MSS/conf_sp_idp/idp/`
    Make sure to insert the key along with its corresponding certificate.

### Configuring the Service Provider and Identity Provider

First, generate the [metadata](https://pysaml2.readthedocs.io/en/latest/howto/config.html#metadata) file for the service provider. To do that, start the Flask application and download the metadata file by following these steps:

1. Navigate to the directory `MSS/conf_sp_idp/sp/app`.
2. Start the Flask application by running `flask run`. The application will listen on port `5000`.
3. Download the metadata file by executing the command: `curl http://localhost:5000/metadata/ -o sp.xml`.
4. Move generated `sp.xml` to dir `conf_sp_idp/idp/`.

After that, regenerate the idp.xml file, copy it over to the Service Provider (SP), and restart the SP Flask application:

5. Go to the directory `MSS/conf_sp_idp/idp/`.
6. Run the command `python make_metadata.py idp_conf.py > idp.xml` in the terminal to generate the `idp.xml` file.
7. Copy the generated `idp.xml` file and replace the existing `idp.xml` file located at `MSS/conf_sp_idp/sp/idp.xml`.

### Running the Application After Configuration

Once you have successfully configured the Service Provider and the Identity Provider, you don't need to follow the above instructions again. To start the application after the initial configuration, follow these steps:

1. Start the Service provider:
 * Navigate to the directory `MSS/conf_sp_idp/sp/app` and run `flask run`.
2. Start the Identity Provider:
 * Navigate to the directory `MSS/conf_sp_idp/idp` and run `python idp.py idp_conf`.

By following the provided instructions, you will be able to set up and configure both the Identity Provider and Service Provider for testing the SSO process.

## Testing SSO

* Once you have successfully launched the server and identity provider, you can begin testing the Single Sign-On (SSO) process. 
* Load in a browser <http://127.0.0.1:5000/>.
* To log in to the service provider through the identity provider, you can use the credentials specified in the `PASSWD` section of the `MSS/conf_sp_idp/idp/idp.py` file. Look for the relevant section in the file to find the necessary login credentials.

## References

* https://pysaml2.readthedocs.io/en/latest/examples/idp.html
