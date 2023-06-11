# pylint: skip-file
# -*- coding: utf-8 -*-
"""
    conf_sp_idp.idp.make_metadata.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Script that creates a SAML2 metadata file from a pysaml2 entity configuration file


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
# Additional Info:
"""
    This file is imported from https://github.com/IdentityPython/pysaml2/blob/master/example/idp2/make_metadata.py
    and customized as MSS requirements. Pylint has been disabled for this imported file.
"""
# Parts of the code

import argparse
import os
import sys

from saml2.config import Config
from saml2.metadata import entities_descriptor
from saml2.metadata import entity_descriptor
from saml2.metadata import metadata_tostring_fix
from saml2.metadata import sign_entity_descriptor
from saml2.sigver import security_context
from saml2.validate import valid_instance

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", dest="valid", help="How long, in days, the metadata is valid from the time of creation")
    parser.add_argument("-c", dest="cert", help="certificate")
    parser.add_argument("-e", dest="ed", action="store_true", help="Wrap the whole thing in an EntitiesDescriptor")
    parser.add_argument("-i", dest="id", help="The ID of the entities descriptor")
    parser.add_argument("-k", dest="keyfile", help="A file with a key to sign the metadata with")
    parser.add_argument("-n", dest="name", default="")
    parser.add_argument("-p", dest="path", help="path to the configuration file")
    parser.add_argument("-s", dest="sign", action="store_true", help="sign the metadata")
    parser.add_argument("-x", dest="xmlsec", help="xmlsec binaries to be used for the signing")
    parser.add_argument("-w", dest="wellknown", help="Use wellknown namespace prefixes")
    parser.add_argument(dest="config", nargs="+")
    args = parser.parse_args()

    valid_for = 0
    nspair = {"xs": "http://www.w3.org/2001/XMLSchema"}
    # paths = [".", "/opt/local/bin"]

    if args.valid:
        # translate into hours
        valid_for = int(args.valid) * 24

    eds = []
    for filespec in args.config:
        bas, fil = os.path.split(filespec)
        if bas != "":
            sys.path.insert(0, bas)
        if fil.endswith(".py"):
            fil = fil[:-3]
        cnf = Config().load_file(fil)
        if valid_for:
            cnf.valid_for = valid_for
        eds.append(entity_descriptor(cnf))

    conf = Config()
    conf.key_file = args.keyfile
    conf.cert_file = args.cert
    conf.debug = 1
    conf.xmlsec_binary = args.xmlsec
    secc = security_context(conf)

    if args.id:
        desc, xmldoc = entities_descriptor(eds, valid_for, args.name, args.id, args.sign, secc)
        valid_instance(desc)
        xmldoc = metadata_tostring_fix(desc, nspair, xmldoc)
        print(xmldoc.decode("utf-8"))
    else:
        for eid in eds:
            if args.sign:
                assert conf.key_file
                assert conf.cert_file
                eid, xmldoc = sign_entity_descriptor(eid, args.id, secc)
            else:
                xmldoc = None

            valid_instance(eid)
            xmldoc = metadata_tostring_fix(eid, nspair, xmldoc)
            print(xmldoc.decode("utf-8"))


if __name__ == "__main__":
    main()
