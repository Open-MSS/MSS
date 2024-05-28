mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
copy /Y "%RECIPE_DIR%\msui.ico" "%PREFIX%\Menu\msui.ico"

; conda-build issue 5311, currently we can't build for windows with pip install
%PYTHON% setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
