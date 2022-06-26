#!/bin/bash

##
## ./start_tutorial.sh python ./tutorial_hexagoncontrol.py
##
export LC_ALL=C

set -e

# the directory of the script
DIR="/tmp/"

# the temp directory used, within $DIR
# omit the -p parameter to create a temporal directory in the default location
WORK_DIR=`mktemp -d -p "$DIR"`

# check if tmp dir was created
if [[ ! "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# deletes the temp directory
function cleanup {      
  killall highlight-pointer
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

# register the cleanup function to be called on the EXIT signal
trap cleanup EXIT

~/bin/highlight-pointer -r 10 &

if [[ "$2" == "./tutorial_mscolab.py" ]]; then
  # ToDo mscolab needs a -Y and a stop
  python $PYTHONPATH/mslib/mscolab/mscolab.py db --seed
  # sleep(2)
  python $PYTHONPATH/mslib/mscolab/mscolab.py start &
  # sleep(2)
fi

export MSUI_CONFIG_PATH=$WORK_DIR

exec "$@"

# sometimes the pointer is still active
killall highlight-pointer
rm -rf "$WORK_DIR"
