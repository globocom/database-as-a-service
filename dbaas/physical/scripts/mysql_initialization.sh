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
}

movedatabase()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Moving the database"
    mv /opt/dbaas/dbdata/* /data/
    die_if_error "Error moving datafiles"
}

filepermission()
{
    chown mysql:mysql /data
    die_if_error "Error changing datadir permission"
    chmod g+r /data
    die_if_error "Error changing datadir permission"
    chmod g+x /data
    die_if_error "Error changing datadir permission"
}

mountdatadisk

if [ "{{MOVE_DATA}}" != "True" ]; then
    movedatabase
fi

filepermission

exit 0