#!/bin/bash

die_if_error()
{
    local err=$?
    if [ "$err" != "0" ]; then
        echo "$*"
        exit $err
    fi
}

setreplication()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Setting the database replication"
    mysql -p{{DBPASSWORD}} <<EOF_DBAAS
    CHANGE MASTER TO
    MASTER_HOST='{{IPMASTER}}',
    MASTER_USER='{{REPLICA_USER}}',
    MASTER_PASSWORD='{{REPLICA_PASSWORD}}',
    MASTER_LOG_FILE='mysql-bin.000003',
    MASTER_LOG_POS=154;
    exit
EOF_DBAAS
    die_if_error "Error setting replication"
}

startreplication()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting the database replication"
    mysql -p{{DBPASSWORD}}<<EOF_DBAAS
    start slave;
    exit
EOF_DBAAS
    die_if_error "Error starting slave"
}

startheartbeatdaemon()
{
    echo ""; echo $(date "+%Y-%m-%d %T") "- Starting heartbeat daemon"
    {{ HEARTBEAT_START_COMMAND }}
    #die_if_error "Error starting heartbeat"
}

setreplication
startreplication
startheartbeatdaemon

exit 0