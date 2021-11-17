#!/bin/bash
case $1 in
normal) 
touch /dev/log 
make run
;;
celery) make run_celery ;;
*) echo "Syntax: run_dev.sh [normal|celery]" ;;
esac