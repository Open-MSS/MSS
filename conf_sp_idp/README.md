## Identity Provider and Service Provider for testing the SSO process

The `conf_sp_idp` designed for testing the Single Sign-On (SSO) process using PySAML2. This folder contains both the Identity Provider (IdP) and Service Provider (SP) implementations.

The Identity Provider was set up following the official documentation of PySAML2, along with examples provided in the repository. Metadata YAML files, as well as key and certificate files, were generated using the built-in tools of PySAML2. Actual key and certificate files can be used in when actual implementation. Please note that this project is intended for testing purposes only.

# Getting started

To get started, follow the guidelines provided within the `sp` (Service Provider) and `idp` (Identity Provider) folders. After installing all the necessary dependencies, simply follow the instructions outlined in the respective README files of each folder.

By following the provided instructions, you will be able to set up and configure both the Identity Provider and Service Provider for testing the SSO process.

# References

* https://pysaml2.readthedocs.io/en/latest/examples/idp.html
