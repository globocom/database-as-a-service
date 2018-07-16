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
    if [ "{{DATABASERULE}}" == "PRIMARY" ]; then
{% if DISK_SIZE_IN_GB < 5.0 %}
        mv /opt/dbaas/dbdata_small/* /data/
{% else %}
        mv /opt/dbaas/dbdata/* /data/
{% endif %}
    else
         mv /opt/dbaas/dbdata_empty/* /data/
    fi
    die_if_error "Error moving datafiles"
}

filerpermission()
{
    chown mongodb:mongodb /data
    die_if_error "Error changing datadir permission"
    chmod g+r /data
    die_if_error "Error changing datadir permission"
    chmod g+x /data
    die_if_error "Error changing datadir permission"
}

if [ "{{MOVE_DATA}}" != "True" ]; then
  movedatabase
fi

if [ "{{DATABASERULE}}" = "ARBITER" ] &&  [ "{{MOVE_DATA}}" = "True" ]; then
   movedatabase
fi

filerpermission

exit 0