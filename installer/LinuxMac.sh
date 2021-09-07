#   mss.installer.LinuxMac
#   ~~~~~~~~~~~~~~~~~~~~~
#
#   This script tries to install conda and/or mss on a Linux or MacOS system automatically.
#
#   This file is part of mss.
#
#   :copyright: Copyright 2021 May Baer
#   :copyright: Copyright 2021 by the mss team, see AUTHORS.
#   :license: APACHE-2.0, see LICENSE for details.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

#!/bin/bash -i
echo "Checking Conda installation..."
condaInstalled="Yes"
conda || { echo "Downloading miniconda3..." &&
   condaInstalled="No" &&
   unameOS=$([ "$(uname -s)" == "Darwin" ] && echo "MacOSX" || echo "Linux") &&
   curl "https://repo.anaconda.com/miniconda/Miniconda3-latest-${unameOS}-x86_64.sh" --output miniconda-installer.sh &&
   echo "Installing miniconda3..." &&
   chmod +x miniconda-installer.sh && script -q -c "./miniconda-installer.sh -u" output.txt &&
   location=$(cat output.txt | grep "PREFIX=" | sed -e "s/PREFIX=//g" | sed -e "s/\x0d//g") && rm output.txt &&
   if [[ $location != "" ]]; then . $location/etc/profile.d/conda.sh; else . ~/.bashrc; fi && conda init &&
   if [[ $SHELL = *zsh ]]; then conda init zsh; fi && rm miniconda-installer.sh &&
   conda || { echo "Conda still not found, please restart your console and try again"; exit 1; }
}

echo "Conda installed"
. $(conda info --base)/etc/profile.d/conda.sh
conda config --add channels conda-forge
conda activate mssenv || {
    echo "mssenv not found, creating..." &&
    conda create -n mssenv mamba -y &&
    conda activate mssenv || { echo "Environment not found, aborting"; exit 1; }
}

echo "Installing mss..."
mamba install mss python -y
mamba list -f mss | grep "conda-forge" || { echo MSS was not successfully installed, aborting; exit 1; }

echo "Done!"
if [[ $condaInstalled = "No" ]]; then echo "Please restart your shell for changes to take effect! 'exec $SHELL'"; fi
echo "To start mss,"
echo "1. Activate your conda environment with this command: 'conda activate mssenv'"
echo "2. Start mss with this command: 'mss'"
