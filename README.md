[![build status](https://travis-ci.org/globocom/database-as-a-service.svg?branch=master)](http://travis-ci.org/globocom/database-as-a-service)

Database as a Service (DBaaS)
===================================

Introduction
============

This is an implementation of a database as a service api written in python + django. It will try to follow some hypermedia concepts throughout the api calls.

Below: Screenshot from the admin user.

**image 1:** Listing databases and their summary informations.

![Listing databases and their summary informations](doc/img/manage_dbs.png "Listing databases and their summary informations")

**image 2:** example database view and all its credentials.

![alt text](doc/img/manage_one_db.png "exampledb database view and all its credentials")


Requirements
============

DBaaS requires the following:

* python >= 2.7.5
* virtualenv >= 1.7.2
* virtualenvwrapper >= 3.5
* mysql server and client, version 5.5.x
* mongo client = 2.4 (used by the clone feature)
* redis (broker for async tasks with celery)
* and all packages in requirements.txt file (there is a shortcut to install them)


Setup docker and docker-compose(optional)
=========================================

* Install [Docker](https://docs.docker.com/engine/installation/)

Setup your local environment
============================

    mkvirtualenv dbaas
    workon dbaas


Install the required python packages by:

    make pip
    
Database setup for migrations:

1. Connect to the local database.
    
        mysql -u root -p <GENERATED-PASSWORD>
2. Change root password to an empty string.     
    
        ALTER USER 'root'@'localhost' IDENTIFIED BY '';

3. Create ```dbaas``` database.
    
        CREATE DATABASE dbaas;
    
Run migrations to mysql database:

    make run_migrate

Install redis and start celery:

    make run_celery

Create the tables structure (see the next item)

## DB

DBaaS uses south to maintain the migrations up-to-date. However, you can
just run syncdb to create the table structures. There is a shortcut to help you with that, including
some minimum operational data on DB.

    make reset_data

## Running all tests on local environment

    make pip && make test


## Running all test with docker( To run this the docker-compose must be avaliable)

    make docker_build && make test_with_docker

## Running the project

    make run

In your browser open the URL: http://localhost:8000/admin/

### Running celery

To run celery locally use the following command:

    cd {APP DIR}
    make run_celery

Documentation
=============

[Definitions](./doc/definitions.md)
-------------------------------------------

[Quickstart](./doc/quickstart.md)
-------------------------------------------

[API](./doc/API.md)
-------------------------------------------

[Drivers](./doc/drivers.md)
-------------------------------------------

[Troubleshooting](./doc/troubleshooting.md)
-------------------------------------------

## License

This project is licensed under the BSD 3-Clause "New" or "Revised" License - read [LICENSE](LICENSE) file for details.
