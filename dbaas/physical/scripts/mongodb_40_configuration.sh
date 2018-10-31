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
# mongodb.conf 4.0

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

    # disable journal
    journal:
        enabled: true

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
   bindIp: {{HOSTADDRESS}}

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

configure_graylog()
{
    if [ $(grep -c CentOS /etc/redhat-release) -ne 0 ]
    then
        sed -i "\$a \$EscapeControlCharactersOnReceive off" /etc/rsyslog.conf
        sed -i "\$a \$template db-log, \"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%	tags: INFRA,DBAAS,MONGODB,{{DATABASENAME}}\"" /etc/rsyslog.conf
        sed -i "\$a*.*                    @{{ GRAYLOG_ENDPOINT }}; db-log" /etc/rsyslog.conf
    else
        echo "\$EscapeControlCharactersOnReceive off" >> /etc/rsyslog.d/dbaaslog.conf
        sed -i "\$a \$template db-log, \"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%	tags: INFRA,DBAAS,MONGODB,{{DATABASENAME}}\"" /etc/rsyslog.d/dbaaslog.conf
        sed -i "\$a*.*                    @{{ GRAYLOG_ENDPOINT }}; db-log" /etc/rsyslog.d/dbaaslog.conf
    fi
    /etc/init.d/rsyslog restart
}

{% if CONFIGFILE_ONLY %}
    createconfigdbfile
{% else %}
    createconfigdbfile
    createmongodbkeyfile
    configure_graylog
{% endif %}

exit 0
