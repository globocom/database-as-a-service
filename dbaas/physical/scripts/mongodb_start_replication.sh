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
    /usr/local/mongodb/bin/mongo {{HOST01.address}}/admin --quiet -uadmindbaas -p{{DBPASSWORD}} <<EOF_DBAAS
    config = {_id: '{{REPLICASETNAME}}',
          members: [
                    {_id: 0, host: '{{HOST01.address}}:27017'},
                    {_id: 1, host: '{{HOST02.address}}:27017'},
                    {_id: 3, host: '{{HOST03.address}}:27017', arbiterOnly: true}
                   ]
         }
    rs.initiate(config);
    exit
EOF_DBAAS
    die_if_error "Error setting replication"
}

if [ "{{DATABASERULE}}" == "PRIMARY" ]; then
    setreplication
fi

exit 0
