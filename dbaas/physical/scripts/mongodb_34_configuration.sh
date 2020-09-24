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
    destination: file
    path: /data/logs/mongodb.log
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
{% if 'mongodb_replica_set' in DRIVER_NAME %}
    # File used to authenticate in replica set environment
    keyFile: /data/mongodb.key
{% else %}
    authorization: enabled
{% endif %}

{% if 'mongodb_replica_set' in DRIVER_NAME %}
########################################
## Replica Set
########################################
replication:
    # Use replica sets with the specified logical set name
    replSetName: {{ REPLICASETNAME }}

    # Custom size for replication operation log in MB.
    oplogSizeMB: {{ configuration.oplogSize.value }}
{% endif %}

EOF_DBAAS
) > {{ CONFIG_FILE_PATH|default:"/data/mongodb.conf" }}
    die_if_error "Error setting mongodb.conf"

    chown mongodb:mongodb {{ CONFIG_FILE_PATH|default:"/data/mongodb.conf" }}
    die_if_error "Error changing mongodb conf file owner"
}

createconfigdbrsyslogfile()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Creating the rsyslog config file"

(cat <<EOF_DBAAS
#mongodb.conf 3.4 rsyslog.d configuration

\$ModLoad imfile
\$InputFileName /data/logs/mongodb.log
\$InputFileTag mongod.27017:
\$InputFileStateFile mongodb-log-dbaas

\$InputFileSeverity info
\$InputFileFacility local0
\$InputRunFileMonitor

EOF_DBAAS
) > /etc/rsyslog.d/mongodb.conf
    die_if_error "Error setting mongodb.conf"
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
    createconfigdbrsyslogfile
    createmongodbkeyfile
{% endif %}

exit 0
