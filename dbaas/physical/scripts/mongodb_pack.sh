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
{% if ENGINE_VERSION|slice:"0:3" == "3.4" %}
# mongodb.conf 3.4

########################################
## Storage configuration
########################################
storage:

    # Location of the database files
    dbPath: /data/data/

    # Alternative directory structure, in which files for each database are kept in a unique directory
    directoryPerDB: true

    # Storage Engine
    engine: wiredTiger

    wiredTiger:
        engineConfig:
            cacheSizeGB: {{ configuration.wiredTiger_engineConfig_cacheSizeGB.value }}

    # small files
    mmapv1:
    {% if DISK_SIZE_IN_GB < 5.0 %}
        smallFiles: true
    {% else %}
        smallFiles: false
    {% endif %}

    # disable journal
    journal:
    {% if DATABASERULE == "ARBITER" %}
        enabled: false
    {% else %}
        enabled: true
    {% endif %}

########################################
## Process Management configuration
########################################
processManagement:
    # Fork the server process and run in background
    fork: true


########################################
## Log Options
########################################
systemLog:
    destination: syslog
    quiet: {{ configuration.quiet.value }}
    verbosity: {{ configuration.logLevel.value }}

########################################
## Net Options
########################################
net:
    http:
        # Allow extended operations at the Http Interface
        enabled: true
        RESTInterfaceEnabled: true
{% if PORT %}
    port: {{ PORT }}
{% endif %}

########################################
## Security
########################################
security:
{% if IS_HA  %}
    # File used to authenticate in replica set environment
    keyFile: /data/mongodb.key
{% else %}
    authorization: enabled
{% endif %}

{% if IS_HA  %}
########################################
## Replica Set
########################################
replication:
    # Use replica sets with the specified logical set name
    replSetName: {{ REPLICASETNAME }}

    # Custom size for replication operation log in MB.
    oplogSizeMB: {{ configuration.oplogSize.value }}
{% endif %}
{% endif %}

{% if ENGINE_VERSION|slice:"0:3" == "3.0" %}
# mongodb.conf 3.0

########################################
## Storage configuration
########################################
storage:

    # Location of the database files
    dbPath: /data/data/

    # Alternative directory structure, in which files for each database are kept in a unique directory
    directoryPerDB: true

    # Storage Engine
    engine: wiredTiger

    # small files
    mmapv1:
    {% if DISK_SIZE_IN_GB < 5.0 %}
        smallFiles: true
    {% else %}
        smallFiles: false
    {% endif %}

    # disable journal
    journal:
    {% if DATABASERULE == "ARBITER" %}
        enabled: false
    {% else %}
        enabled: true
    {% endif %}

########################################
## Process Management configuration
########################################
processManagement:
    # Fork the server process and run in background
    fork: true


########################################
## Log Options
########################################
systemLog:
    destination: syslog
    quiet: {{ configuration.quiet.value }}
    verbosity: {{ configuration.logLevel.value }}

########################################
## Net Options
########################################
net:
    http:
        # Allow extended operations at the Http Interface
        enabled: true
        RESTInterfaceEnabled: true
{% if PORT %}
    port: {{ PORT }}
{% endif %}

########################################
## Security
########################################
security:
{% if IS_HA  %}
    # File used to authenticate in replica set environment
    keyFile: /data/mongodb.key
{% else %}
    authorization: enabled
{% endif %}

{% if IS_HA  %}
########################################
## Replica Set
########################################
replication:
    # Use replica sets with the specified logical set name
    replSetName: {{ REPLICASETNAME }}

    # Custom size for replication operation log in MB.
    oplogSizeMB: {{ configuration.oplogSize.value }}
{% endif %}
{% endif %}

{% if ENGINE_VERSION|slice:"0:3" == "2.4" %}
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

{% if IS_HA  %}
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
{% endif %}


EOF_DBAAS
) > /data/mongodb.conf
    die_if_error "Error setting mongodb.conf"

    chown mongodb:mongodb /data/mongodb.conf
    die_if_error "Error changing mongodb conf file owner"
}

createconfigdbfile

exit 0
