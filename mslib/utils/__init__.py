# -*- coding: utf-8 -*-
"""

    mslib.utils
    ~~~~~~~~~~~~~~

    Collection of utility routines for the Mission Support System.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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

import logging


class FatalUserError(Exception):
    def __init__(self, error_string):
        logging.debug("%s", error_string)


def setup_logging(args):
    logger = logging.getLogger()
    # this is necessary as "someone" has already initialized logging, preventing basicConfig from doing stuff
    for ch in logger.handlers:
        logger.removeHandler(ch)

    debug_formatter = logging.Formatter("%(asctime)s (%(module)s.%(funcName)s:%(lineno)s): %(levelname)s: %(message)s")
    default_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Console handler (suppress DEBUG by default)
    ch = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(debug_formatter)
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
        ch.setFormatter(default_formatter)
    logger.addHandler(ch)
    # File handler (always on DEBUG level)
    # TODO: Change this to write to a rotating log handler (so that the file size
    # is kept constant). (mr, 2011-02-25)
    if args.logfile:
        logfile = args.logfile
        try:
            fh = logging.FileHandler(logfile, "w")
        except (OSError, IOError) as ex:
            logger.error("Could not open logfile '%s': %s %s", logfile, type(ex), ex)
        else:
            logger.setLevel(logging.DEBUG)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(debug_formatter)
            logger.addHandler(fh)


# ToDo likely this can be removed in python 3 because that uses unicode
# modified Version from minidom, https://github.com/python/cpython/blob/2.7/Lib/xml/dom/minidom.py
# MSS needed to change all writings as unicode not str
from xml.dom.minidom import _write_data, Node
# Copyright © 2001-2018 Python Software Foundation. All rights reserved.
# Copyright © 2000 BeOpen.com. All rights reserved.


def writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent + "<" + self.tagName)

    attrs = self._get_attributes()

    for a_name in sorted(attrs.keys()):
        writer.write(" %s=\"" % a_name)
        _write_data(writer, attrs[a_name].value)  # nosec, we take care of writing correct XML
        writer.write("\"")
    if self.childNodes:
        writer.write(">")
        if (len(self.childNodes) == 1 and self.childNodes[0].nodeType == Node.TEXT_NODE):
            # nosec, we take care of writing correct XML
            self.childNodes[0].writexml(writer, '', '', '')
        else:
            writer.write(newl)
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write(indent)
        writer.write("</%s>%s" % (self.tagName, newl))
    else:
        writer.write("/>%s" % (newl))


def conditional_decorator(dec, condition):
    def decorator(func):
        if not condition:
            # Return the function unchanged, not decorated.
            return func
        return dec(func)
    return decorator


def prefix_route(route_function, prefix='', mask='{0}{1}'):
    """
    https://stackoverflow.com/questions/18967441/add-a-prefix-to-all-flask-routes/18969161#18969161
    Defines a new route function with a prefix.
    The mask argument is a `format string` formatted with, in that order:
      prefix, route
    """
    def newroute(route, *args, **kwargs):
        """ prefix route """
        return route_function(mask.format(prefix, route), *args, **kwargs)
    return newroute
