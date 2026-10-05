# -*- coding: utf-8 -*-
"""

    mslib.mscolab.api.attachments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    File types of chat attachments and profile images, shared by the MSColab server and msui.

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

# Formats of images, by the format PIL detects, with the extension they are stored with
IMAGE_FORMATS = {"PNG": "png", "JPEG": "jpg", "GIF": "gif", "BMP": "bmp", "WEBP": "webp"}
IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "gif", "bmp", "webp")

# Default of the server setting MSCOLAB_ATTACHMENT_EXTENSIONS. Left out on purpose: files a browser can run
# (html, svg, xml, js), files Windows can run (exe, msi, bat, cmd, ps1, vbs, hta, scr, lnk, jar),
# office files with macros (docm, xlsm, pptm) and archives, which can contain any of these.
DEFAULT_ATTACHMENT_EXTENSIONS = (
    # flight tracks of MSS and of its import and export plugins
    "ftml", "csv", "txt", "kml", "gpx",
    # science data
    "nc", "nc4", "h5", "json",
    # documents
    "pdf", "md", "docx", "xlsx", "pptx", "odt", "ods", "odp",
    # images
    *IMAGE_EXTENSIONS,
    # videos
    "mp4", "mov",
)


def file_extension(filename):
    """The extension of a file name, lower case and without the dot, "" if it has none"""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[1].lower() if "." in name.strip(".") else ""


def normalized_extensions(extensions):
    """The extensions of a setting, lower case and without dots, e.g. (".PDF", "csv") -> {"pdf", "csv"}"""
    return {extension.strip().lstrip(".").lower() for extension in extensions}
