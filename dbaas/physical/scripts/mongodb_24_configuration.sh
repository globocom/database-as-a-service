#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

createconfigdbfile()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the database config file"

(cat <<EOF_DBAAS
# mongodb.conf 2.4


########################################
## Basic database configuration
########################################

# Location of the database files
dbpath=/data/data/

# Alternative directory structure, in which files for each database are kept in a unique directory
directoryperdb=true

# Fork the server process and run in background
fork = true

# small files
{% if DISK_SIZE_IN_GB < 5.0 %}
smallfiles = true
{% else %}
smallfiles = false
{% endif %}

{% if PORT %}
port = {{PORT}}
{% endif %}

########################################
## Log Options
########################################

syslog = True
quiet = {{ configuration.quiet.value }}

########################################
## Administration & Monitoring
########################################

# Allow extended operations at the Http Interface
rest = true

{% if 'mongodb_replica_set' in DRIVER_NAME %}
########################################
## Replica Sets
########################################

# Use replica sets with the specified logical set name
replSet={{REPLICASETNAME}}

# File used to authenticate in replica set environment
keyFile=/data/mongodb.key

# Custom size for replication operation log in MB.
oplogSize = {{ configuration.oplogSize.value }}
{% else %}
########################################
## Security
########################################

# Turn on/off security.  Off is currently the default
auth = true
{% endif %}

{% if DATABASERULE == "ARBITER" %}
# disable journal
nojournal=yes
{% endif %}

EOF_DBAAS
) > /data/mongodb.conf
    die_if_error "Error setting mongodb.conf"

    chown mongodb:mongodb /data/mongodb.conf
    die_if_error "Error changing mongodb conf file owner"
}

createmongodbkeyfile()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the mongodb key file"

(cat <<EOF_DBAAS
{{MONGODBKEY}}
EOF_DBAAS
) >  /data/mongodb.key
    die_if_error "Error setting mongodb key file"

    chown mongodb:mongodb /data/mongodb.key
    die_if_error "Error changing mongodb key file owner"
    chmod 600 /data/mongodb.key
    die_if_error "Error changing mongodb key file permission"

}


{% if CONFIGFILE_ONLY %}
    createconfigdbfile
{% else %}
    createconfigdbfile
    createmongodbkeyfile
{% endif %}

exit 0
