# -*- coding: utf-8 -*-
"""

    mslib.utils.time
    ~~~~~~~~~~~~~~~~

    Collection of functions all around time handling.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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
import datetime
import isodate
import logging


def parse_iso_datetime(string):
    try:
        result = isodate.parse_datetime(string)
    except isodate.ISO8601Error:
        result = isodate.parse_date(string)
        result = datetime.datetime.fromordinal(result.toordinal())
        logging.debug("ISO String Couldn't be Parsed.\n ISO8601Error Encountered.")
    if result.tzinfo is not None:
        result = result.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return result


def parse_iso_duration(string):
    return isodate.parse_duration(string)


JSEC_START = datetime.datetime(2000, 1, 1)


def datetime_to_jsec(dt):
    """
    Calculate seconds since Jan 01 2000.
    """
    delta = dt - JSEC_START
    total = delta.days * 3600 * 24
    total += delta.seconds
    total += delta.microseconds * 1e-6
    return total


def jsec_to_datetime(jsecs):
    """
    Get the datetime from seconds since Jan 01 2000.
    """
    return JSEC_START + datetime.timedelta(seconds=jsecs)


def compute_hour_of_day(jsecs):
    date = JSEC_START + datetime.timedelta(seconds=jsecs)
    return date.hour + (date.minute / 60.) + (date.second / 3600.)


def utc_to_local_datetime(utc_datetime):
    return utc_datetime.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
