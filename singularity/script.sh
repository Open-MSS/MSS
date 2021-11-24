#!/bin/bash

set -e


if [ "$1" = 'MSS' ]; then

    echo "initialize demodata and start services"
    echo ""
    mswms_demodata --create 
    mswms --port 8081  &
    sleep 3
    mscolab db --init
    sleep 3
    mscolab start &
    sleep 3
    mss 

fi

exec "$@"
