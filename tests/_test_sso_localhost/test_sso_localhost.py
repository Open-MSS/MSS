import os
import subprocess
import time

from urllib.parse import urljoin
from bs4 import BeautifulSoup

import requests
import pytest

os.environ['TEST_CASES_ENABLED'] = 'true'

@pytest.fixture(scope='session')
def client():
    """
    Fixture to set up and tear down the test client

    This fixture sets up the test environment by performing the following steps:
    1. Generates key and certificate files for the service provider (SP) and the
    identity provider (IDP).
    2. Starts the SP and downloads the metadata file from SP using curl.
    3. Generates the IDP metadata for the SP.
    4. Starts the IDP.
    5. Configures the SP and creates necessary database tables.
    6. Yields the test client object for making requests to the application.
    7. Cleans up the environment by removing generated files, terminating the IDP process,
       and resetting the environment variable.

    The client fixture provides the test client object within a test context, allowing the tests
    to interact with the application as a client.
    """


    # Configure flask service provider for testing

    # Generate key and certificate for service provider (SP)
    process_gen_crt_key_sp = (
    'openssl req -x509 -newkey rsa:4096 -keyout mslib/auth_client_sp/test_key_sp.key '
    '-out mslib/auth_client_sp/test_crt_sp.crt -sha256 -days 3650 -nodes '
    '-subj "/C=XX/ST=State/L=City/O=Company/OU=CompanySection/CN=CommanName"'
    )

    subprocess.run(process_gen_crt_key_sp, shell=True, check=True)
    # Generate key and certificate for identity provider (IDP)
    process_gen_crt_key_idp = (
    'openssl req -x509 -newkey rsa:4096 -keyout mslib/idp/test_key_idp.key '
    '-out mslib/idp/test_crt_idp.crt -sha256 -days 3650 -nodes '
    '-subj "/C=XX/ST=State/L=City/O=Company/OU=CompanySection/CN=CommonName"'
    )

    subprocess.run(process_gen_crt_key_idp, shell=True, check=True)



    # Start the service provider (SP)
    cmd_start_sp = ['python', 'mslib/auth_client_sp/app/app.py']
    process_sp = subprocess.Popen(cmd_start_sp)

    # Wait for the service provider (SP) to start
    time.sleep(5)

    # Download the metadata file from SP using curl
    cmd_curl_metadata_sp = ['curl', 'http://localhost:5000/metadata/', '-o',
                            'mslib/idp/test_sp.xml']
    subprocess.run(cmd_curl_metadata_sp, check=True)

    # Stop the service provider (SP)
    process_sp.kill()

    # Generate IDP metadata for service provider (SP)
    cmd_make_metadata_idp = ['make_metadata', 'mslib/idp/idp_conf.py']
    output_metadata_idp = 'mslib/auth_client_sp/test_idp.xml'
    with open(output_metadata_idp, 'w', encoding='utf-8') as file:
        subprocess.run(cmd_make_metadata_idp, stdout=file, check=True)

    # Configure identity provider (IDP)

    # Start the identity provider (IDP)
    process_start_idp = subprocess.Popen(['python', 'mslib/idp/idp.py', 'idp_conf'])

    # Wait for the identity provider (IDP) to start
    time.sleep(5)

    # Start the SP

    # pylint: disable=C0415
    from mslib.auth_client_sp.app.app import app, db

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create necessary database tables
            yield client
            db.session.remove()  # Remove the session after the test
            db.drop_all()  # Drop all database tables

    # Forcefully terminate the identity provider (IDP) process
    process_start_idp.kill()



    # Delete the generated files
    os.remove('mslib/idp/test_key_idp.key')
    os.remove('mslib/idp/test_crt_idp.crt')
    os.remove('mslib/auth_client_sp/test_key_sp.key')
    os.remove('mslib/auth_client_sp/test_crt_sp.crt')
    os.remove('mslib/idp/test_sp.xml')
    os.remove('mslib/auth_client_sp/test_idp.xml')

    # Reset the environment variable
    os.environ.pop('TEST_CASES_ENABLED', None)


# Test case to add a user to the database
def test_db_add_user(client):
    """
    Test adding a user to the database.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If adding the user to the database or the commit operation
    doesn't behave as expected.

    Description:
    - Adds a user with a specified email address to the database.
    - Asserts that the commit operation returns None, indicating a successful
    addition to the database.

    This test case verifies the functionality of adding a user to the database by
    checking the result of the commit operation. It ensures that the user is 
    successfully added to the database without errors.
    """

    # pylint: disable=C0415
    from mslib.auth_client_sp.app.app import User, db
    user = User(email='testemail@address.com')
    db.session.add(user)
    assert None is db.session.commit()


def test_index(client):
    """
    Test the index page of Service Provider.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the index page or response doesn't behave as expected.

    Description:
    - Performs a GET request to the index page.
    - Asserts that the response has a status code of 200.
    - Asserts that the response data contains the expected string.

    This test case verifies the functionality of the index page by checking the status code
    and the presence of the expected string in the response data.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Example Simple SP" in response.data


def test_sp_login_redirect(client):
    """
    Test the service provider (SP) login redirect.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the login redirect or response doesn't behave as expected.

    Description:
    - Performs a GET request to the SP login page.
    - Asserts that the response has a status code of 303 (Redirect).
    - Asserts that the response data contains the expected string indicating a login redirect.

    This test case verifies the functionality of the login redirect from the service provider (SP)
    by checking the status code and the presence of the expected string in the response data.
    """
    response = client.get("/login/")
    assert response.status_code == 303
    assert b"sso/redirect?SAMLRequest" in response.data

def get_login_redirect_idp_url(client):
    """
    Helper function to get the IDP login URL from the login redirect
    """
    response = client.get("/login/")
    return response.headers["Location"]

def test_invalid_login_idp(client):
    """
    Test an invalid login flow with the IDP.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the login flow or response doesn't behave as expected.

    Description:
    - Retrieves the IDP login URL.
    - Performs a GET request to the IDP login page.
    - Asserts that the response contains the expected text and has a status code of 200.
    - Parses the HTML response of the IDP login page.
    - Extracts the form action URL and other form fields from the login page.
    - Constructs the absolute URL for the form action in the login page.
    - Fills in the form data with an invalid username and password.
    - Performs a POST request to the IDP login page with invalid credentials.
    - Asserts the response of the invalid login attempt.

    This test case verifies the functionality of an invalid login flow with the IDP,
    including the submission of incorrect login credentials and the assertion of
    the response for the failed login attempt.
    """

    idp_login_url = get_login_redirect_idp_url(client)

    # Perform GET request to the IDP login page
    response_idp_login = requests.get(idp_login_url, verify=False, timeout=30)

    # Assert the response of the IDP login page
    assert "IDP test login" in response_idp_login.text
    assert response_idp_login.status_code == 200

    # Parse the HTML response of the IDP login page
    soup_login_page = BeautifulSoup(response_idp_login.text, "html.parser")

    # Extract the form action URL and other form fields from the login page
    form_idp_login = soup_login_page.find("form")
    idp_login_action_url = form_idp_login["action"]

    # Construct the absolute URL for the form action in the login page
    action_url = urljoin(idp_login_url, idp_login_action_url)

    form_data_idp_login = {}
    for input_field in form_idp_login.find_all("input"):
        if input_field.get("name"):
            field_name = input_field["name"]
            field_value = input_field.get("value", "")
            form_data_idp_login[field_name] = field_value

    # Fill in the form data with the invalid username and password
    form_data_idp_login["login"] = 'invaliduser'
    form_data_idp_login["password"] = 'noneuser'

    # Perform POST request to the IDP login page with invalid credentials
    response_idp_logged = requests.post(action_url, data=form_data_idp_login,
                                        verify=False, timeout=30)

    # Assert the response of the invalid login attempt
    assert response_idp_logged.status_code == 401
    assert "Unknown user or wrong password" in response_idp_logged.text

def test_valid_login_idp(client):
    """
    Test a valid login flow with the IDP.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the login flow or response doesn't behave as expected.

    Description:
    - Retrieves the IDP login URL.
    - Performs a GET request to the IDP login page.
    - Asserts that the response contains the expected text and has a status code of 200.
    - Extracts the form action URL and other form fields from the login page.
    - Fills in the form data with a valid username and password.
    - Performs a POST request to the IDP login page with valid credentials.
    - Asserts the SAML response.
    - Extracts the form action URL and other form fields from the SAML response.
    - Performs a POST request to the service provider (SP) with the SAML response.
    - Asserts that the response has a status code of 302, indicating a redirect to the profile page.
    - Asserts that the response text contains the string 'href="/profile/'.

    This test case verifies the functionality of a valid login flow with the IDP,
    including the successful submission of login credentials, extraction and
    submission of the SAML response, and the subsequent redirection to the profile page.
    """
    idp_login_url = get_login_redirect_idp_url(client)

    # Perform GET request to the IDP login page
    response_idp_login = requests.get(idp_login_url, verify=False, timeout=30)

    # Assert the response of the IDP login page
    assert "IDP test login" in response_idp_login.text
    assert response_idp_login.status_code == 200

    # Extract the form action URL and other form fields from the login page
    form_idp_login = BeautifulSoup(response_idp_login.text, "html.parser").find("form")
    idp_login_action_url = form_idp_login["action"]

    # Construct the absolute URL for the form action in the login page
    action_url = urljoin(idp_login_url, idp_login_action_url)

    # Fill in the form data with the valid username and password
    form_data_idp_login = {
        input_field["name"]: input_field.get("value", "")
        for input_field in form_idp_login.find_all("input")
        if input_field.get("name")
    }
    form_data_idp_login["login"] = 'testuser'
    form_data_idp_login["password"] = 'qwerty'

    # Perform POST request to the IDP login page with valid credentials
    response_idp_logged = requests.post(action_url, data=form_data_idp_login,
                                        verify=False, timeout=30)

    # Assert the SAML response
    assert response_idp_logged.status_code == 200
    assert "SAMLResponse" in response_idp_logged.text

    # Extract the form action URL and other form fields from the SAML response
    form_saml_res = BeautifulSoup(response_idp_logged.text, "html.parser").find("form")
    action_url_saml_res = form_saml_res["action"]

    form_data_saml_res = {
        input_field["name"]: input_field.get("value", "")
        for input_field in form_saml_res.find_all("input")
        if input_field.get("name")
    }

    # Perform POST request to the SP with the SAML response
    response_sp = client.post(action_url_saml_res, data=form_data_saml_res)
    assert response_sp.status_code == 302  # Redirect to profile page
    assert 'href="/profile/' in response_sp.text



def test_profile_authenticated(client):
    """
    Test the profile page for an authenticated user.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the profile page doesn't behave as expected.

    Description:
    - Sends a GET request to the "/profile/" endpoint.
    - Asserts that the response status code is 200, indicating a successful request.
    - Asserts that the response text contains the string 'Hello',
    indicating the presence of a greeting on the profile page.

    This test case verifies that the profile page is accessible
    to an authenticated user by checking the response status code
    and ensuring that the greeting is displayed on the page.
    """
    response = client.get("/profile/")
    assert response.status_code == 200  # Successful request
    assert 'Hello' in response.text



def test_logout(client):
    """
    Test the logout functionality.

    Parameters:
    - client: The test client object for making requests to the application.

    Raises:
    AssertionError: If the logout process doesn't behave as expected.

    Description:
    - Sends a GET request to the "/logout/" endpoint.
    - Asserts that the response status code is 302, indicating a redirect to the index page.
    - Asserts that the response text contains the string 'href="/"',
    indicating a link to the index page.

    This test case verifies that the logout process works correctly by 
    checking the response status code and
    the presence of the link to the index page in the response.
    """
    response = client.get("/logout/")
    assert response.status_code == 302  # Redirect to index page
    assert 'href="/"' in response.text
