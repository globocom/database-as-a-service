#!/bin/bash

[[ $# -ne 12 ]] && echo "usage: db_orig user_orig pass_orig host_orig port_orig db_dest user_dest pass_dest host_dest port_dest path_of_dump engine" && exit 1


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


echo -e "\n#### db to be cloned #### \n name: $db2clone \n user: $user2clone \n password: $pass2clone \n host: $host2clone \n\n\n##### db dest ##### \n name: $db_dest \n user: $user_dest \n password: $pass_dest \n host: $host_dest \n\n path of dump: $path_of_dump \n engine: $engine\n\n\n generated at: `date`\n" > "$path_of_dump/$$.txt"

for a in {1..300}
do
    dd if=/dev/zero of="$path_of_dump/$$.dump" bs=1k count=100000
    sleep 1
    rm -f $path_of_dump/$$.dump
done

exit 0