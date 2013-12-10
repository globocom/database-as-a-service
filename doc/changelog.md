# Changelog


## 0.0.1

* support to manage mongodb database and users
* role based authorization
* ldap authentication
* basic api
* a minimum EC2 api integration

## 0.0.2

* bug fix when creating database with an existing name
* removed team management from user perspective
* fix django-simple-audit version

## 0.0.3

* fix django-simple-audit to a working version with m2m auditing
* team filter in user view
* role filter in user view
* add the possibility to specify a monitoring_url for a hostname
* showing environment and plan in database listing
* removed slug field from project (it is not used...)