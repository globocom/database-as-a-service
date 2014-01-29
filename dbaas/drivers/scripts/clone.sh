#!/bin/bash

[[ $# -ne 12 ]] && echo "usage: db_orig user_orig pass_orig host_orig port_orig db_dest user_dest pass_dest host_dest port_dest path_of_dump engine" && exit 1

basedir=$(dirname $0)

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
engine=${12}

if [ $engine = 'mongodb' ]
then
    $basedir/mongodb_clone.sh ${1} ${2} ${3} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11}
    ret=$?
fi


if [ $engine = 'mysql' ]
then
    $basedir/mysql_clone.sh ${1} ${2} ${3} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11}
    ret=$?
fi

exit ${ret}