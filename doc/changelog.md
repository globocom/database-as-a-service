# Changelog

## 0.0.5

* several bug fixes in databaseinfra creation (filtering plan for selected engine and filtering env for selected plan)
* dashboard for sysadmins
* basic support for mysql engine
* showing database status
* users with "regular" role can manage databases in quarantine
* preventing from hitting the database unduly in database view listing
* automatically purging databases older than a specific value
* removing api root url redirect to github

## 0.0.4

* users can be in more than one team
* dba can now change the team accountable for a database
* filter to find user without a team
* database status in database listing
* some mysql tests
* method to list databases in a specific driver (implemented in mongodb and mysql)
* showing plan and environment in database listing
* google analytics


## 0.0.3

* fix django-simple-audit to a working version with m2m auditing
* team filter in user view
* role filter in user view
* add the possibility to specify a monitoring_url for a hostname
* showing environment and plan in database listing
* removed slug field from project form (it is not used...)
* inform user for how long the database will be put in quarantine

## 0.0.2

* bug fix when creating database with an existing name
* removed team management from user perspective
* fix django-simple-audit version

## 0.0.1

* support to manage mongodb database and users
* role based authorization
* ldap authentication
* basic api
* a minimum EC2 api integration

