#!/bin/sh

mkdir -p "${PREFIX}/Menu"
cp "${RECIPE_DIR}/menu.json" "${PREFIX}/Menu/${PKG_NAME}_menu.json"

"${PYTHON}" -m pip install . --no-deps -vv
