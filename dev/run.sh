#!/bin/bash

FILE=/code/dev/debug_lib/lib.list

if [[ -f $FILE ]]
then
    cat $FILE | while read line || [[ -n $line ]]
    do  
        pip uninstall -y $line
        cd /opt/lib/$line
        python setup.py develop
    done
fi

cd /code
touch /code/dev/log
make run