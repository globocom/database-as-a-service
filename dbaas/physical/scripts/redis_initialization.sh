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

mountdatadisk_sentinel()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Mounting data disk"
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


{% if ONLY_SENTINEL or not HAS_FAAS_DISK %}
    mountdatadisk_sentinel
{% else %}
    mountdatadisk
{% endif %}

exit 0
