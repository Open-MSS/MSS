mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
copy /Y "%RECIPE_DIR%\msui.ico" "%PREFIX%\Menu\msui.ico"


%PYTHON% setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
