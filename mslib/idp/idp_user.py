# -*- coding: utf-8 -*-
"""

    mslib.idp.idp_user.py
    ~~~~~~~~~~~~~~~~~~~~~

    User data and additional attributes for test users and affiliates.

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
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

USERS = {
    "testuser": {
        "sn": "Testsson",
        "givenName": "Test",
        "eduPersonAffiliation": "student",
        "eduPersonScopedAffiliation": "student@example.com",
        "eduPersonPrincipalName": "test@example.com",
        "uid": "testuser",
        "eduPersonTargetedID": ["one!for!all"],
        "c": "SE",
        "o": "Example Co.",
        "ou": "IT",
        "initials": "P",
        "co": "co",
        "mail": "mail",
        "noreduorgacronym": "noreduorgacronym",
        "schacHomeOrganization": "example.com",
        "email": "test@example.com",
        "displayName": "Test Testsson",
        "labeledURL": "http://www.example.com/test My homepage",
        "norEduPersonNIN": "SE199012315555",
        "postaladdress": "postaladdress",
        "cn": "cn",
    },
    "roland": {
        "sn": "Hedberg",
        "givenName": "Roland",
        "email": "roland@example.com",
        "eduPersonScopedAffiliation": "staff@example.com",
        "eduPersonPrincipalName": "rohe@example.com",
        "uid": "rohe",
        "eduPersonTargetedID": ["one!for!all"],
        "c": "SE",
        "o": "Example Co.",
        "ou": "IT",
        "initials": "P",
        "mail": "roland@example.com",
        "displayName": "P. Roland Hedberg",
        "labeledURL": "http://www.example.com/rohe My homepage",
        "norEduPersonNIN": "SE197001012222",
    },
    "babs": {
        "surname": "Babs",
        "givenName": "Ozzie",
        "email": "babs@example.com",
        "eduPersonAffiliation": "affiliate"
    },
    "upper": {
        "surname": "Jeter",
        "givenName": "Derek",
        "email": "upper@example.com",
        "eduPersonAffiliation": "affiliate"
    },
}

EXTRA = {
    "roland": {
        "eduPersonEntitlement": "urn:mace:swamid.se:foo:bar",
        "schacGender": "male",
        "schacUserPresenceID": "skype:pepe.perez",
    }
}
