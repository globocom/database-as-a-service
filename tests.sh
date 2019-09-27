#!/bin/bash
# which mysql
# ls
# echo -n 'waiting mysql start'
# while ! mysql -h $DBAAS_DATABASE_HOST -uroot -p$DBAAS_DATABASE_PASSWORD -e "SHOW DATABASES"
# do
#   echo -n .
#   sleep 1
# done
#
# ps -ef | grep mysql
# echo 'MYSQL STARTED!!!!'
#
# # Create DATABASE
# echo "create database IF NOT EXISTS dbaas;" | mysql -h $DBAAS_DATABASE_HOST -uroot -p$DBAAS_DATABASE_PASSWORD

# Create user on mongo
python add_user_admin_on_mongo.py

# Run tests
make test
# bash
