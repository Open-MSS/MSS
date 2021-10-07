# -*- coding: utf-8 -*-
"""

    mslib.utils._tests.test_time
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.utils.time

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
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
import logging
import datetime
import mslib.utils.time as time

LOGGER = logging.getLogger(__name__)


class TestParseTime(object):
    def test_parse_iso_datetime(self):
        assert time.parse_iso_datetime("2009-05-28T16:15:00") == datetime.datetime(2009, 5, 28, 16, 15)

    def test_parse_iso_duration(self):
        assert time.parse_iso_duration('P01W') == datetime.timedelta(days=7)


class TestTimes(object):
    """
    tests about times
    """

    def test_datetime_to_jsec(self):
        assert time.datetime_to_jsec(datetime.datetime(2000, 2, 1, 0, 0, 0, 0)) == 2678400.0
        assert time.datetime_to_jsec(datetime.datetime(2000, 1, 1, 0, 0, 0, 0)) == 0
        assert time.datetime_to_jsec(datetime.datetime(1995, 1, 1, 0, 0, 0, 0)) == -157766400.0

    def test_jsec_to_datetime(self):
        assert time.jsec_to_datetime(0) == datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        assert time.jsec_to_datetime(3600) == datetime.datetime(2000, 1, 1, 1, 0, 0, 0)
        assert time.jsec_to_datetime(-157766400.0) == datetime.datetime(1995, 1, 1, 0, 0, 0, 0)

    def test_compute_hour_of_day(self):
        assert time.compute_hour_of_day(0) == 0
        assert time.compute_hour_of_day(86400) == 0
        assert time.compute_hour_of_day(3600) == 1
        assert time.compute_hour_of_day(82800) == 23
