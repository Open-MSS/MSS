# Flask Service Provider with PySAML2 Integration

This is a simple Flask service provider that allows for single sign-on (SSO) authentication using PySAML2.

## Features

- Integration with PySAML2 for SSO authentication.
- Securely handles SAML assertions and authentication responses.
- Provides routes for login, logout, and profile endpoints.
- Uses SQLite database for user management.
- Supports both HTTP Redirect and HTTP POST bindings for SAML responses.

## Getting Started

To start the service provider, follow these steps:

1. Navigate to the `conf_sp_idp/sp` directory.
2. Run the following command to start the flask server:
    `flask run`
    This command will launch the service provider and make it accessible.
3. Access the service provider using the provided URL and begin the SSO authentication process.

That's it! You're now ready to use the Flask Service Provider for SSO authentication.
