mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
copy /Y "%RECIPE_DIR%\msui.ico" "%PREFIX%\Menu\msui.ico"


%PYTHON% -m pip install . --no-deps -vv
if errorlevel 1 exit 1
