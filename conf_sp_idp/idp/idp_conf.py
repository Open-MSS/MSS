# -*- coding: utf-8 -*-
"""

    conf_sp_idp.idp.idp_conf.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SAML2 IDP configuration with bindings, endpoints, and authentication contexts.

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Parts of the code

import os.path

from saml2 import BINDING_HTTP_ARTIFACT
from saml2 import BINDING_HTTP_POST
from saml2 import BINDING_HTTP_REDIRECT
from saml2 import BINDING_SOAP
from saml2 import BINDING_URI
from saml2.saml import NAME_FORMAT_URI
from saml2.saml import NAMEID_FORMAT_PERSISTENT
from saml2.saml import NAMEID_FORMAT_TRANSIENT


try:
    from saml2.sigver import get_xmlsec_binary
except ImportError:
    get_xmlsec_binary = None

if get_xmlsec_binary:
    XMLSEC_PATH = get_xmlsec_binary(["/opt/local/bin"])
else:
    XMLSEC_PATH = '/usr/bin/xmlsec1'

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def full_path(local_file):
    """Return the full path by joining the BASEDIR and local_file."""

    return os.path.join(BASEDIR, local_file)

HOST = 'localhost'
PORT = 8088

HTTPS = True

if HTTPS:
    BASE = f"https://{HOST}:{PORT}"
else:
    BASE = f"http://{HOST}:{PORT}"

# HTTPS cert information
SERVER_CERT = "crt_idp.crt"
SERVER_KEY = "key_idp.key"
CERT_CHAIN = ""
SIGN_ALG = None
DIGEST_ALG = None
#SIGN_ALG = ds.SIG_RSA_SHA512
#DIGEST_ALG = ds.DIGEST_SHA512


CONFIG = {
    "entityid": f"{BASE}/idp.xml",
    "description": "My IDP",
    #"valid_for": 168,
    "service": {
        "aa": {
            "endpoints": {
                "attribute_service": [
                    (f"{BASE}/attr", BINDING_SOAP)
                ]
            },
            "name_id_format": [NAMEID_FORMAT_TRANSIENT,
                               NAMEID_FORMAT_PERSISTENT]
        },
        "aq": {
            "endpoints": {
                "authn_query_service": [
                    (f"{BASE}/aqs", BINDING_SOAP)
                ]
            },
        },
        "idp": {
            "name": "Rolands IdP",
            "sign_response": True,
            "sign_assertion": True,
            "endpoints": {
                "single_sign_on_service": [
                    (f"{BASE}/sso/redirect", BINDING_HTTP_REDIRECT),
                    (f"{BASE}/sso/post", BINDING_HTTP_POST),
                    (f"{BASE}/sso/art", BINDING_HTTP_ARTIFACT),
                    (f"{BASE}/sso/ecp", BINDING_SOAP)
                ],
                "single_logout_service": [
                    (f"{BASE}/slo/soap", BINDING_SOAP),
                    (f"{BASE}/slo/post", BINDING_HTTP_POST),
                    (f"{BASE}/slo/redirect", BINDING_HTTP_REDIRECT)
                ],
                "artifact_resolve_service": [
                    (f"{BASE}/ars", BINDING_SOAP)
                ],
                "assertion_id_request_service": [
                    (f"{BASE}/airs", BINDING_URI)
                ],
                "manage_name_id_service": [
                    (f"{BASE}/mni/soap", BINDING_SOAP),
                    (f"{BASE}/mni/post", BINDING_HTTP_POST),
                    (f"{BASE}/mni/redirect", BINDING_HTTP_REDIRECT),
                    (f"{BASE}/mni/art", BINDING_HTTP_ARTIFACT)
                ],
                "name_id_mapping_service": [
                    (f"{BASE}/nim", BINDING_SOAP),
                ],
            },
            "policy": {
                "default": {
                    "lifetime": {"minutes": 15},
                    "attribute_restrictions": None, # means all I have
                    "name_form": NAME_FORMAT_URI,
                    #"entity_categories": ["swamid", "edugain"]
                },
            },
            "subject_data": "./idp.subject",
            "name_id_format": [NAMEID_FORMAT_TRANSIENT,
                               NAMEID_FORMAT_PERSISTENT]
        },
    },
    "debug": 1,
    "key_file": full_path("./key_idp.key"),
    "cert_file": full_path("./crt_idp.crt"),
    "metadata": {
        "local": [full_path("./sp.xml")],
    },
    "organization": {
        "display_name": "Organization Display Name",
        "name": "Organization name",
        "url": "http://www.example.com",
    },
    "contact_person": [
        {
            "contact_type": "technical",
            "given_name": "technical",
            "sur_name": "technical",
            "email_address": "technical@example.com"
        }, {
            "contact_type": "support",
            "given_name": "Support",
            "email_address": "support@example.com"
        },
    ],
    # This database holds the map between a subject's local identifier and
    # the identifier returned to a SP
    "xmlsec_binary": XMLSEC_PATH,
    #"attribute_map_dir": "../attributemaps",
    "logging": {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s] %(message)s",
            },
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "level": "DEBUG",
                "formatter": "simple",
            },
        },
        "loggers": {
            "saml2": {
                "level": "DEBUG"
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": [
                "stderr",
            ],
        },
    },
}

# Authentication contexts

    #(r'verify?(.*)$', do_verify),

CAS_SERVER = "https://cas.umu.se"
CAS_VERIFY = f"{BASE}/verify_cas"
PWD_VERIFY = f"{BASE}/verify_pwd"

AUTHORIZATION = {
    "CAS" : {"ACR": "CAS", "WEIGHT": 1, "URL": CAS_VERIFY},
    "UserPassword" : {"ACR": "PASSWORD", "WEIGHT": 2, "URL": PWD_VERIFY}
}
