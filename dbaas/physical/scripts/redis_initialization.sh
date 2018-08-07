#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

filerpermission()
{
    mkdir -p /data/data
    die_if_error "Error creating data dir"
    chown redis:redis /data
    die_if_error "Error changing datadir permission"
    chown -R redis:redis /data/data
    die_if_error "Error changing datadir permission"
    chmod g+r /data
    die_if_error "Error changing datadir permission"
    chmod g+x /data
    die_if_error "Error changing datadir permission"
}

filerpermission

exit 0
