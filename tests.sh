#!/bin/bash
echo -n 'waiting mysql start'
while ! /usr/local/mysql/bin/mysql -h $DBAAS_DATABASE_HOST -uroot -p$DBAAS_DATABASE_PASSWORD -e "SHOW DATABASES"
do
  echo -n .
  sleep 1
done

echo 'MYSQL STARTED!!!!'

# Create DATABASE
echo "create database IF NOT EXISTS dbaas;" | /usr/local/mysql/bin/mysql -h $DBAAS_DATABASE_HOST -uroot -p$DBAAS_DATABASE_PASSWORD

# Create user on mongo
python add_user_admin_on_mongo.py

# Run tests
make test
# bash
