# -*- coding: utf-8 -*-
"""

    tests._test_api.test_attachments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for mslib.mscolab.api.attachments, the file types of chat attachments.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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
import pytest

from mslib.mscolab.api.attachments import (
    DEFAULT_ATTACHMENT_EXTENSIONS, IMAGE_EXTENSIONS, IMAGE_FORMATS, file_extension, normalized_extensions,
)


@pytest.mark.parametrize("filename, extension", [
    ("track.ftml", "ftml"),
    ("Track.FTML", "ftml"),
    ("archive.tar.gz", "gz"),
    ("C:\\data\\track.csv", "csv"),
    ("/home/user/notes.v2.txt", "txt"),
    ("README", ""),
    (".bashrc", ""),
    ("name.", ""),
    ("", ""),
    (None, ""),
])
def test_file_extension(filename, extension):
    assert file_extension(filename) == extension


def test_normalized_extensions():
    assert normalized_extensions([".PDF", " csv ", "ftml"]) == {"pdf", "csv", "ftml"}


def test_default_attachment_extensions():
    for extension in ("ftml", "csv", "txt", "kml", "gpx", "nc", "nc4", "h5", "json", "pdf", "md", "docx", "xlsx",
                      "pptx", "odt", "ods", "odp", "mp4", "mov", *IMAGE_EXTENSIONS):
        assert extension in DEFAULT_ATTACHMENT_EXTENSIONS
    # files a browser or Windows can run, macros, archives
    for extension in ("html", "htm", "xhtml", "svg", "xml", "js", "exe", "msi", "bat", "cmd", "ps1", "vbs", "hta",
                      "scr", "lnk", "jar", "docm", "xlsm", "pptm", "zip", "tar", "gz", "7z"):
        assert extension not in DEFAULT_ATTACHMENT_EXTENSIONS
    assert normalized_extensions(DEFAULT_ATTACHMENT_EXTENSIONS) == set(DEFAULT_ATTACHMENT_EXTENSIONS)


def test_image_formats_stored_with_image_extensions():
    assert set(IMAGE_FORMATS.values()) <= set(IMAGE_EXTENSIONS)
