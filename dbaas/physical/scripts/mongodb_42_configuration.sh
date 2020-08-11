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
# mongodb.conf 4.2

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
    destination: file
    path: /data/logs/mongodb.log
    quiet: {{ configuration.quiet.value }}
    verbosity: {{ configuration.logLevel.value }}


########################################
## Net Options
########################################
net:
    bindIp: {{HOSTADDRESS}}
{% if PORT %}
    port: {{ PORT }}
{% endif %}
{% if SSL_CONFIGURED %}
    tls:
        #mode: allowTLS #step 1
        #mode: preferTLS #step 2
        #mode: requireTLS #step 3
        mode: {% if SSL_MODE_ALLOW %}allowTLS{% endif %}{% if SSL_MODE_PREFER %}preferTLS{% endif %}{% if SSL_MODE_REQUIRE %}requireTLS{% endif %}
        certificateKeyFile: {{ INFRA_SSL_CERT }}
        CAFile: {{ MASTER_SSL_CA }}
        allowConnectionsWithoutCertificates: true
{% endif %}

########################################
## Security
########################################
security:
{% if 'mongodb_replica_set' in DRIVER_NAME %}
    # File used to authenticate in replica set environment
    keyFile: /data/mongodb.key
    {% if SSL_CONFIGURED %}
    #clusterAuthMode: sendKeyFile #step 1
    #clusterAuthMode: sendX509 #setp 2
    #clusterAuthMode: x509 #step 3
    clusterAuthMode: {% if SSL_MODE_ALLOW %}sendKeyFile{% endif %}{% if SSL_MODE_PREFER %}sendX509{% endif %}{% if SSL_MODE_REQUIRE %}x509{% endif %}
    {% endif %}
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
#mongodb.conf 4.0 rsyslog.d configuration

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
    createconfigdbrsyslogfile
    createmongodbkeyfile
    configure_graylog
{% endif %}

exit 0
