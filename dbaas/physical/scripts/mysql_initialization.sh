#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

movedatabase()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Moving the database"
    mv /opt/dbaas/dbdata/* /data/
    die_if_error "Error moving datafiles"
}

filepermission()
{
    mkdir -p /data/logs
    die_if_error "Error creating logs dir"
    chown mysql:mysql /data
    die_if_error "Error changing datadir permission"
    chown mysql:mysql /data/logs
    die_if_error "Error changing logs dir permission"
    chmod g+r /data
    die_if_error "Error changing datadir permission"
    chmod g+x /data
    die_if_error "Error changing datadir permission"
}

if [ "{{MOVE_DATA}}" != "True" ]; then
    movedatabase
fi

filepermission

exit 0