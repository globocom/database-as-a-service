#!/bin/bash

[[ $# -ne 11 ]] && echo "usage: db_orig user_orig pass_orig host_orig port_orig db_dest user_dest pass_dest host_dest port_dest path_of_dump" && exit 1

db2clone=${1}
user2clone=${2}
pass2clone=${3}
host2clone=${4}
port2clone=${5}

db_dest=${6}
user_dest=${7}
pass_dest=${8}
host_dest=${9}
port_dest=${10}

pass2clone2=$(echo "${pass2clone#*=}")
pass_dest2=$(echo "${pass_dest#*=}")
path_of_dump=${11}/${db_dest}_$(echo $RANDOM)

echo $(date "+%Y-%m-%d %T") "- Creating temporary dir..."
mkdir -p ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on creating temporary dir"
    exit ${ret}
fi

echo ""; echo $(date "+%Y-%m-%d %T") "- Dumping source database..."
mongodump -h ${host2clone} --port ${port2clone} -u ${user2clone} -p ${pass2clone2} -d ${db2clone} --authenticationDatabase admin -o ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on dumping source database"
    rm -rf ${path_of_dump}
    exit ${ret}
fi

echo ""; echo $(date "+%Y-%m-%d %T") "- Deleting users from dump..."
rm -f ${path_of_dump}/${db2clone}/system.users.metadata.json
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on deleting users from dump"
    rm -rf ${path_of_dump}
    exit ${ret}
fi

rm -f ${path_of_dump}/${db2clone}/system.users.bson
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on deleting users from dump"
    rm -rf ${path_of_dump}
    exit ${ret}
fi

echo ""; echo $(date "+%Y-%m-%d %T") "- Restoring target database..."
mongorestore -h ${host_dest} --port ${port_dest} -u ${user_dest} -p ${pass_dest2} -d ${db_dest} --authenticationDatabase admin ${path_of_dump}/${db2clone}
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on restoring target database"
    rm -rf ${path_of_dump}
    exit ${ret}
fi

echo ""; echo $(date "+%Y-%m-%d %T") "- Deleting temporary files..."
rm -rf ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    echo $(date "+%Y-%m-%d %T") "- ERROR on deleting temporary files"
    exit ${ret}
fi

exit 0
