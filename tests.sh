#!/bin/bash

# Create DATABASE
echo "create database IF NOT EXISTS dbaas;" | mysql -h mysqldb56 -u root -p123

# Create user on mongo
python add_user_admin_on_mongo.py

# Run tests
make test
