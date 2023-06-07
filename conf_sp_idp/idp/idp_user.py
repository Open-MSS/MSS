# -*- coding: utf-8 -*-
"""
This module contains user data and extra information.

The USERS dictionary contains information about users, such as their names,
affiliations, email addresses, etc.
The EXTRA dictionary contains additional information for specific users.

imported from https://github.com/IdentityPython/pysaml2/blob/master/example/idp2/idp_user.py
"""

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
