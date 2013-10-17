Database as a Service (DBaas)
===================================

Introduction
============

This is an implementation of a database as a service api written in python + django. It will try to follow some hypermedia concepts throughout the api calls.

Initially it will only support MongoDB.

Status
=======

In development (alpha)

Setup your local environment
============================

    mkvirtualenv dbaas
    workon dbaas
    
    
You will also need to create a sitecustomize.py file with the following content in 
yours python's lib directory.

    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")

Then, finally

    make check_environment
    
Install the required python packages.

    make pip
    
Create the tables structure (see the next item)

## DB

DBaaS uses simple-db-migrate to maintain the migrations up-to-date. However, for now, you can
just run syncdb to create the table structures. There is a make shortcut to help you with that

    make db_drop_and_create

## Running the project

    make run
    
In your browser open the URL: http://localhost:8000/admin/

## Running the tests

Before running the test, makes sure that you have mongod running and a user admin created with password 123456.

    db = db.getSiblingDB('admin')

    db.addUser( { user: "admin",
                  pwd: "123456",
                  roles: [ "userAdminAnyDatabase", "clusterAdmin", "readWriteAnyDatabase", "dbAdminAnyDatabase" ] } )

Then install all the required packages

    make pip
    
Run it!

    make test

