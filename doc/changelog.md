# Changelog

## 0.0.78
* Add Migration from MySQL Flipper to MySQL FoxHA

## 0.0.73
* Add framework to engine topology
* Add MySQL FOXHA topology

## 0.0.72
* Add step on mysql migration to start mk-heartbeat-daemon
* Upgrade mongodb (3.0.8 to 3.0.12)

## 0.0.71
* Return True if the seconds delay is less than 2
* Change the default attempts on check_replication_and_switch function

## 0.0.70
* Config Backup Log Database

## 0.0.69
* Set new mongodb instances to hidden

## 0.0.68
* General bug fixes

## 0.0.67
* Created at column being displayed at databases list

## 0.0.66
* Change database admin: refactor database mongo upgrade to call task with name args
* Improve upgrade task history arguments
* Disable zabbix alarms in upgrade_mongodb_24_to_30 function

## 0.0.65
* Upgrade MongoDB - HA
* Improve resize message - HA
* Database: add new button to provide mongodb engine version upgrade
* Change physical engine: Add engine_upgrade option
* Add support for engine version upgrade plan
* Change pkg version
* General bug fixes

## 0.0.64
* kombu 3.0.30
* python-ldap 2.4.22
* dbaas_credentials 1.0.7
* dbaas_nfsaas 0.6.7
* zabbix version 0.2.8
* dbaas_cloudstack 0.7.8
* Improve restore snapshot
* Add disable/enable zabbix alarms on tasks which may impact on host availability
* BSD-3 License file added
* Add filter by engine type
* Add missing migration
* Add button to start analysis on resource use reports
* Add task "Analyzing all databases"
* Save restored snapshot
* Add team field on database change list
* use update_fields on save instance/database
* Improvements on exception handling, remove unused vars, some filters and indexes
* Small fixes

## 0.0.63
* pymongo 3.0.3
* Change dbaas_credentials 1.0.5
* acl_api 0.0.52
* improve css
* Add team field on analyze repository
* database migration - add engine and remove engine_type field on plan
* remove engine_type field, add engine_type property and engine field
* Add new property: engine
* Add task to send email to users when the database is overestimated
* Add msg on false alarm
* Improve ux
* Add engine, environment and databaseinfra options on filter and metrics link on repository list
* Add volume alarm field
* Check if service is working
* Add analyze service and analyze repository
* Check if the switch primary step was ok
* Update source_instances on workflow_dict
* Create task to update laas team
* Add step to delete old acls
* Setup steps to stop old instances and start new instances
* Change resize to update databaseinfra max database size when it is a redis infra
* Small fixes
* General bug fixes

## 0.0.62
* General bug fixes

## 0.0.61
* Fix region migrations settings

## 0.0.60
* Zabbix 0.2.7

## 0.0.59
* Zabbix 0.2.6

## 0.0.58
* Zabbix 0.2.5

## 0.0.57
* Remove bundle picking from for loop
* Change dbaas_zabbix version
* Small fixes

## 0.0.56
* Zabbix 0.2.3
* Add non database instances

## 0.0.55
* dbaas-aclapi 0.0.47
* dbaas_nfsaas 0.6.6
* dbaas_cloudstack 0.7.7
* dbaas_dbmonitor 0.1.7
* improve start vm, workflow and get_database_agents
* Add resize with high availability and helper function to rollback resize
* Add clean unused data
* New function check_replication_and_switch
* Add normalize series to metrics graph data
* Add time filters for host metrics
* Add acl binds file
* Check user permission before showing the add delete link
* Create model ExtraDns and add extra dns signals to insert and remove dbmonitor's reference
* Change metric detail to automatically get granularity options
* Small fixes

## 0.0.54
* Add support for volume migration task
* Improve volume migration task
* Improve is_beeing used to query for currently executing tasks
* Volume migration ha
* Add method to deal with switch master
* Add methods to deal with databaseinfra instances

## 0.0.53
* dbaas_nfsaas 0.6.4
* Volume migrate only secondary instance
* Setup volume migration to deal with ha databases
* Add chown on start database
* Initial steps for volume migration
* New NFS HostAttr attributes
* Improve mysql replication methods
* Change workflow settings
* Add replication info

## 0.0.52
* Fix master-slave configuration
* General bug fixes

## 0.0.51
* Add new param to show metric filters or not

## 0.0.50
* dbaas_aclapi 0.0.46
* Add filters to graph options
* Changing mysql test to retrieve database password from settings.py
* Add redis region migration
* Add support for redis on new configuration scripts
* Add to mysql support for new plan scripts
* Change mongodb initi database to use new user data scripts
* Small fixes

## 0.0.49
* Improve database backup lookup
* Add buttons to help database region migration

## 0.0.48
* Add check to show recovery button

## 0.0.47
* Add check to backup_databases_now

## 0.0.46
* dbaas_nfsaas 0.6.1
* dbaas_flipper 0.0.9
* dbaas_aclapi 0.0.39
* dbaas_cloudstack version to 0.7.1
* Save snapshot info
* Add initial support to database migration task revoke
* Add new field on migration detail to know its direction
* Add engine on database region migration list view
* Add button to make databases backup
* Improve tsuru validation: check database allocation limit
* Add new method to know whether the database is being used elsewhere
* Add support for redis_sentinel
* Add mysql HA support
* Add function to get replication information from files
* Add step to update dbaas metadata
* Add snapshot restore
* Fix bug: this step was removing all secondary ips instead of only the olds
* Add new flipper steps
* Add mysql start replication step
* Add new scripts to RestoreBackupOnTargets
* Add steps to revoke nfs access, to remove nfs snapshot and to create secondary ips for target_hosts
* add mysql steps and mysql steps region migration
* Add start td_agent step
* Small fixes and improvements
* General bug fixes

## 0.0.45
* Comment unused call

## 0.0.44
* dbaas_dnsapi 0.1.0
* dbaas_cloudstack 0.7.0
* acl_api version 0.0.15c
* Create functions to build scripts
* Add initial method to initialize migration
* Add 'test_bash_error'
* Add mongodb utils
* Improve database_region_migration
* Add region migration detail
* Add new steps: remove_old_instances, switch_dns, switch_primary, check_database_binds and create_virtualmachines
* Add new status - ERROR
* Add rollback
* New exception on undo to prevent destroy database
* Change schedule next step logic
* mongodb migration step one
* Add database migration steps
* Add mongodb steps database migration
* Add get_current_step and get_engine_steps methods
* Improve physical models to make region migration easier
* Check if databasebind is being destroyed
* Improve transaction commit
* Change service bind to be atomic
* Improve tsuru bind/unbind
* Small fixes
* General bug fixes

## 0.0.43
* Change is_waiting_to_run to get AttributeError exception

## 0.0.42
* Maintenance hosts

## 0.0.39
* fix tsuru bugs

## 0.0.38
* Add celery worker to TaskHistory context
* Change redis connection string
* General bug fixes

## 0.0.37
* Fix resize button
* Create TaskHistory object outside celery task
* Description and project are obligatory for databases created from admin interface.

## 0.0.36
* Updated to Django 1.6.10(and its deps)
* Updated Celery to 3.1.17
* Fix pre-provisioned database deletion and improve database deletion proccess


## 0.0.35
* Redis HA
* Fix database api (deleting database)

## 0.0.34
* Change Celery Health String
* Bug Fix Zabbix api

## 0.0.33
* Add 'acive' option to plan api
* Improve redis driver
* Initial redis clone
* Refactor Workflow engine
* Change zabbix version
* Add tests

## 0.0.32
* Bug Fix metrics name database
* Bug Fix deleting backup

## 0.0.31
* Clone to different environments and plans
* New Engine Redis

## 0.0.30
* Bug fix resize mysql infra

## 0.0.29
* improve workflow
* add resize for cloudstack databases

## 0.0.28
* bug fix: tsuru routes
* change graphite metrics params
* add support for same database name in environment
* add metrics link only for cloudstack databases
* add log link

## 0.0.27
* Add support to Graphite metrics

## 0.0.26
* Change dbaas_credentials version (bug fix)

## 0.0.25
* Integration with network api
* Integration with LaaS (initially disabled)

## 0.0.24
* Initial integration with acl_api

## 0.0.23
* Remove plan from database name+environment check
* Call CreateDbMonitor on DEPLOY_MONGO

## 0.0.22
* Integration with Tsuru
* PyMongo 2.7.2
* Celery 3.1.14

## 0.0.21
* [Closed issues on 0.0.21]

## 0.0.20
* [Closed issues on 0.0.20]


## 0.0.19
* bug fix: typo on taskhistory
* change database admin to use database status column

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

[Closed issues on 0.0.20]: https://github.com/globocom/database-as-a-service/issues?q=milestone%3ASprint4.Q3.2014

[Closed issues on 0.0.21]: https://github.com/globocom/database-as-a-service/issues?q=milestone%3ASprint5.Q3.2014+is%3Aclosed
