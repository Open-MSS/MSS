# -*- coding: utf-8 -*-
"""

    mslib.utils.release_info
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Shows by a github API call information about the latest release

    This file is part of MSS.

    :copyright: Copyright 2024 Reimar Bauer
    :copyright: Copyright 2024 by the MSS team, see AUTHORS.
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
import logging
import requests

from mslib.version import __version__ as installed_version


def get_latest_release():
    # GitHub API URL for the MSS Release
    url = "https://api.github.com/repos/Open-MSS/MSS/releases/latest"

    try:
        # Make a GET request to the GitHub API
        response = requests.get(url, timeout=(1, 1))
        response.raise_for_status()  # Raise an error for non-200 status codes

        # Extract the JSON response
        release_data = response.json()

        # Extract the latest release tag and name
        latest_release = {
            'tag_name': release_data['tag_name'],
            'release_name': release_data['name'],
            'published_at': release_data['published_at'],
            'url': release_data['html_url']
        }
        return latest_release

    except requests.exceptions.RequestException as e:
        logging.debug(f"Error fetching release data: {e}")
        return None


def check_for_new_release():
    no_new_release_found = f"{datetime.date.today()}: No new release found."
    try:
        latest_release = get_latest_release()
    except TimeoutError as e:
        logging.debug(f"Error fetching release data: {e}")
        latest_release = None

    if latest_release is None or latest_release['tag_name'] == installed_version:
        return no_new_release_found, False

    github_url = f'<a href="{latest_release["url"]}#target">{latest_release["url"]}</a>'
    return ' | '.join([
        f"New release found: {latest_release['release_name']} ({latest_release['tag_name']})",
        f"Published at: {latest_release['published_at']}",
        f"Release URL: {github_url}",
    ]), True
