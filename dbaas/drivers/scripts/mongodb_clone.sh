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

path_of_dump=${11}

mongodump -h ${host2clone} --port ${port2clone} -u ${user2clone} -p ${pass2clone} -d ${db2clone} --authenticationDatabase admin -o ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}/${db2clone}
    exit ${ret}
fi

rm ${path_of_dump}/${db2clone}/system.users.metadata.json
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}/${db2clone}
    exit ${ret}
fi

rm ${path_of_dump}/${db2clone}/system.users.bson
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}/${db2clone}
    exit ${ret}
fi

mongorestore -h ${host_dest} --port ${port_dest} -u ${user_dest} -p ${pass_dest} -d ${db_dest} --authenticationDatabase admin ${path_of_dump}/${db2clone}
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}/${db2clone}
    exit ${ret}
fi

rm -rf ${path_of_dump}/${db2clone}
ret=$?
if [ ${ret} -ne 0 ]
then
    exit ${ret}
fi

exit 0
