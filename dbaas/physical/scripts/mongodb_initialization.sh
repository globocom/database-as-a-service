#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

mountdatadisk()
{
    if [ "{{DATABASERULE}}" != "ARBITER" ]; then
        echo ""; echo $(date "+%Y-%m-%d %T") "- Mounting data disk"
        sed '/data/d' "/etc/fstab"
        echo "{{EXPORTPATH}}    /data nfs defaults,bg,intr,nolock 0 0" >> /etc/fstab
        die_if_error "Error setting fstab"

        if mount | grep /data > /dev/null; then
            umount /data
            die_if_error "Error umount /data"
        fi
        mount /data
        die_if_error "Error mounting /data"

        wcl=$(mount -l | grep data | grep nfs | wc -l)
        if [ "$wcl" -eq 0 ]
        then
            echo "Could not mount /data"
            exit 100
        fi
    else
        echo ""; echo $(date "+%Y-%m-%d %T") "- Arbiter does not mount data disk"
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

if [ "{{DATABASERULE}}" != "ARBITER" ]; then
    mountdatadisk
fi

if [ "{{MOVE_DATA}}" != "True" ]; then
  movedatabase
fi

if [ "{{DATABASERULE}}" = "ARBITER" ] &&  [ "{{MOVE_DATA}}" = "True" ]; then
   movedatabase
fi

filerpermission

exit 0