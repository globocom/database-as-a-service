# Changelog

## 0.0.18
* background tasks to update database and its instances status
* dashboard alert status on dbinfra
* bug fix: when a database was down the dashboard did not know what to do
* insert error code in the end of taskhistory
* change args on taskhistory to show more user friendly information

## 0.0.17
* mysql ha on cloudstack
* create a task to check whether celery is running
* improve exception handling on workflow
* backup only slave instances


## 0.0.16
* add workflow engine
* add a backup management tool
* bug fix: plans and environments were not being listed on the databaseinfra edit screen
 

## 0.0.15
* add cloudstack mysql single and cluster

## 0.0.14
* bug fix: databaseinfra form was not listing plans

## 0.0.13
* cloudstack integration
* zabbix integration
* bug fix: credential user should be equal to the db
* credential manager

## 0.0.12
* show endpoint on database edit page
* bug fix: emails were not being sent

## 0.0.11
* Change engine colors on dashboard
* Improve login page, ldap message.
* Description field on project
* bug fix: when cloning databases a new databaseinfra is passed to it
* Team email can't be blank
* Improve dashboard, show database status on index page


## 0.0.10
* notify the team when the database exceeded the limit of plan or based  in a threshold
* debug message about the steps executed by clone script

## 0.0.9
* clone database
* notification of database infra usage
* using ckeditor in plan description field, allowing the admin to write rich content or anchor links.
* bug fix: when the database hang the connection, status is not cached.
* bug fix: allow databases with the same name but with different engines.
* bug fix: database infra allocation algorithm should consider only active instances.

## 0.0.8
* terms of use

## 0.0.7
* bug fix to render box "My actions"
* bug fix HTML code
* show overall databases usage per team and environment
* link to monitor url in dashboard
* implemented search box in fields database name, team and project

## 0.0.6

* mysql engine user's creation should be constrained per instance and not per database as in mongodb
* change dashboard layout to a tabular view
* database creation allocation limit per team
* upgrading django simple audit version (improvements in m2m audit)

## 0.0.5

* several bug fixes in databaseinfra creation (filtering plan for selected engine and filtering env for selected plan)
* dashboard for sysadmins
* basic support for mysql engine
* showing database status
* users with "regular" role can manage databases in quarantine
* preventing from hitting the database unduly in database listing's view
* automatically purging databases older than a specific value
* removing api root url redirect to github
* created email field in team

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

