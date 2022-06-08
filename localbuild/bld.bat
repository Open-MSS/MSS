set MENU_DIR=%PREFIX%\Menu
if not exist %MENU_DIR% mkdir %MENU_DIR%
if errorlevel 1 exit 1
copy %SRC_DIR%\Menu\msui_shortcut.json %MENU_DIR%\msui_shortcut.json
if errorlevel 1 exit 1
copy %SRC_DIR%\Menu\mss.ico %MENU_DIR%\mss.ico
if errorlevel 1 exit 1
%PYTHON% setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
