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

mkdir -p ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    exit ${ret}
fi

mysqldump -h ${host2clone} --port ${port2clone} -u ${user2clone} -p${pass2clone2} --routines ${db2clone} > ${path_of_dump}/mysql.dump
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}
    exit ${ret}
fi

mysql -h ${host_dest} --port ${port_dest} -u ${user_dest} -p${pass_dest2} ${db_dest} < ${path_of_dump}/mysql.dump
ret=$?
if [ ${ret} -ne 0 ]
then
    rm -rf ${path_of_dump}
    exit ${ret}
fi

rm -rf ${path_of_dump}
ret=$?
if [ ${ret} -ne 0 ]
then
    exit ${ret}
fi


exit 0