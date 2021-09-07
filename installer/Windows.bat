::    mss.installer.Windows
::    ~~~~~~~~~~~~~~~~~~~~~
::
::    This script tries to install conda and/or mss on a Windows system automatically.
::
::    This file is part of mss.
::
::    :copyright: Copyright 2021 May Baer
::    :copyright: Copyright 2021 by the mss team, see AUTHORS.
::    :license: APACHE-2.0, see LICENSE for details.
::
::    Licensed under the Apache License, Version 2.0 (the "License");
::    you may not use this file except in compliance with the License.
::    You may obtain a copy of the License at
::
::       http://www.apache.org/licenses/LICENSE-2.0
::
::    Unless required by applicable law or agreed to in writing, software
::    distributed under the License is distributed on an "AS IS" BASIS,
::    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
::    See the License for the specific language governing permissions and
::    limitations under the License.

@echo off
set script=%~f0
echo Checking Conda installation...
where conda
if %errorlevel% == 0 (goto condainstalled)

:installconda
echo Checking existing conda installs not in path...
set a="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Anaconda3 (64-bit)\Anaconda Prompt (anaconda3).lnk"
set b="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Anaconda3 (64-bit)\Anaconda Prompt (miniconda3).lnk"
set c="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Anaconda3 (32-bit)\Anaconda Prompt (anaconda3).lnk"
set d="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Anaconda3 (32-bit)\Anaconda Prompt (miniconda3).lnk"
if exist %a% if "%1" neq "a" if "%1" neq "b" if "%1" neq "c" if "%1" neq "d" call "cmd /c" %a% "& %script:"=% a" & exit 0
if exist %b% if "%1" neq "b" if "%1" neq "c" if "%1" neq "d" call "cmd /c" %b% "& %script:"=% b" & exit 0
if exist %c% if "%1" neq "c" if "%1" neq "d" call "cmd /c" %c% "& %script:"=% c" & exit 0
if exist %d% if "%1" neq "d" call "cmd /c" %d% "& %script:"=% d" & exit 0

where conda
if %errorlevel% == 0 (goto condainstalled)

echo Downloading miniconda3...
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OSBIT=32BIT || set OSBIT=64BIT
if %OSBIT%==32BIT curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe --output miniconda-installer.exe
if %OSBIT%==64BIT curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe --output miniconda-installer.exe
echo Installing miniconda3 (just use the default settings if you are unsure)...
start /wait miniconda-installer.exe
del "miniconda-installer.exe"
start /i Windows.bat & exit 0

:condainstalled
echo Conda installed
call conda.bat config --add channels conda-forge
call conda.bat activate mssenv
if not %errorlevel% == 0 (
    echo mssenv not found, creating...
    call conda.bat create -n mssenv mamba -y
    call conda.bat activate mssenv
    if errorlevel 1 (echo Environment not found, aborting & pause & exit /B 1)
)

:envexists
echo Installing mss...
call mamba install mss python -y
call mamba list -f mss| findstr /i /e "conda-forge"
if not %errorlevel% == 0 (echo MSS was not successfully installed, aborting & pause & exit /B 1)

echo Done! To start mss, 
echo 1. Activate your conda environment with this command: "conda activate mssenv"
echo 2. Start mss with this command: "mss"
pause
