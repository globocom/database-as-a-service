Database as a Service (DBaaS)
===================================

Introduction
============

This is an implementation of a database as a service api written in python + django. It will try to follow some hypermedia concepts throughout the api calls.

Below: Screenshot from the admin user.

image 1: Listing databases and their summary informations

![Listing databases and their summary informations](doc/img/manage_dbs.png "Listing databases and their summary informations")

image 2: example database view and all its credentials

![alt text](doc/img/manage_one_db.png "exampledb database view and all its credentials")


Requirements
============

DBaaS requires the following:

* python >= 2.7.5
* virtualenv >= 1.7.2
* virtualenvwrapper >= 3.5
* and all packages in requirements.txt file (there is a shortcut to install them)


Setup your local environment
============================

    mkvirtualenv dbaas
    workon dbaas


Install the required python packages.

    make pip
    
Create the tables structure (see the next item)

## DB

DBaaS uses south to maintain the migrations up-to-date. However, you can
just run syncdb to create the table structures. There is a shortcut to help you with that, including 
some minimum operational data on DB.

    make reset_data

## Running all tests

Before running the test, makes sure that you have mongod running and a user admin created with password 123456.

    db = db.getSiblingDB('admin')

    db.addUser( { user: "admin",
                  pwd: "123456",
                  roles: [ "userAdminAnyDatabase", "clusterAdmin", "readWriteAnyDatabase", "dbAdminAnyDatabase" ] } )

Then install all the required packages

    make pip
    
Run it!

    make test

## Running the project

    make run

In your browser open the URL: http://localhost:8000/admin/


Documentation
=============

[Definitions](./doc/definitions.md)
-------------------------------------------

[Quickstart](./doc/quickstart.md)
-------------------------------------------

[API](./doc/API.md)
-------------------------------------------

[Changelog](./doc/changelog.md)
-------------------------------------------