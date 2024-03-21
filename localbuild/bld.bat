mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
%PYTHON% setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
