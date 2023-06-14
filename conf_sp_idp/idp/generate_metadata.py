# -*- coding: utf-8 -*-
"""

    conf_sp_idp.idp.generate_metadata.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This provides a function to run the make_metadata tool 
    from pysaml2 and save the output to a file.

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
    :copyright: Copyright 2023- by the MSS team, see AUTHORS.
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

import sys
import os
import subprocess
import re

def run_make_metadata():
    """
    Runs the make_metadata tool from pysaml2 and saves the output to a file.

    This function executes the make_metadata tool, captures the output, and extracts
    the XML content. The XML content is then saved to the specified output file
    in the service provider.

    Returns:
        None
    """
    python_executable = sys.executable
    tool_name = 'make_metadata'
    tool_path = os.path.join(os.path.dirname(python_executable), tool_name)
    command = [python_executable, tool_path, 'idp_conf.py']

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        xmls = re.findall(r'<[^>]+>.*?</[^>]+>', output.decode('utf-8'), re.DOTALL)

        output_file_path = '../sp/idp.xml'
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.writelines(xmls)

        print("Output written successfully ! to 'idp.xml' in the 'conf_sp_idp/sp/app/' directory.")
    except subprocess.CalledProcessError as error:
        print("Error:", error.output.decode('utf-8'))

if __name__ == "__main__":
    run_make_metadata()
