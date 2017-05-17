#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

startdatabase()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database"
    /etc/init.d/mongodb start > /dev/null
    die_if_error "Error starting database"
    sleep 10
}

startdatabase

exit 0