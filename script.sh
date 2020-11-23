#!/bin/sh

/opt/conda/envs/mssenv/bin/mswms_demodata
/opt/conda/envs/mssenv/bin/mscolab_demodata --init

/opt/conda/envs/mssenv/bin/mswms --port 8081  &
/opt/conda/envs/mssenv/bin/mscolab &
