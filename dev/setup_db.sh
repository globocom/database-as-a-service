#!/bin/bash

if [ -z "$1" ]; then
    echo "No argument supplied. No dumps will be restored."
    exit 0
fi

echo "apllying dump file $1"

docker-compose up -d dev_mysqldb57
sleep 30 # @TODO wait mysql script

cat $1 | docker-compose exec -T dev_mysqldb57 mysql -u root -p123 dbaas

echo "delete from maintenance_databaserestoreinstancepair;
delete from maintenance_databaserestore;
delete from maintenance_databasecreate;
delete from logical_credential;
delete from logical_database;
delete from backup_snapshot;
delete from physical_ip;
delete from physical_vipinstancegroup;
delete from physical_vip;
delete from physical_instance;
delete from physical_volume;
delete from physical_host;
delete from physical_databaseinfraparameter;
delete from dbaas_dnsapi_databaseinfradnslist;
delete from physical_databaseinfra;" | docker-compose exec -T dev_mysqldb57 mysql -u root -p123 dbaas

docker-compose down 

exit 0