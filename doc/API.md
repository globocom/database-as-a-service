The API allows you to maintain yours databases.

## Getting Started

I assumed you know about [REST API](http://en.wikipedia.org/wiki/Representational_state_transfer) and [JSON](http://en.wikipedia.org/wiki/JSON). But if you don't know, don't worry about because I give you examples using `curl` or you can access api using your web browser too. There is a beatiful interface to help you to understand it.

To ensure you will be able to run all examples, they are based on sample data provided by `make reset_data` command.

Currently, only basic authentication is supported. So I recommend you use HTTPS.

* [Database](#database)
   * [Create new database](#post-apidatabase)
   * [List all databases](#get-apidatabase)
   * [Get database info](#get-apidatabasesome_id)
   * [Delete database](#delete-apidatabasesome_id)
* [Credential](#credential)
   * [Create new credential](#post-apicredential)
   * [List all credentials](#get-apicredential)
   * [Show password](#get-apicredentialsome_id)
   * [Reset password](#post-apicredentialsome_idreset_password)
   * [Delete credential](#delete-apicredentialsome_id)

## Database
This resource represents a database. Databases can be created on different engines.

| Fields | Description | Required? | Read only? |
| ---- |:-------------| -----:| -----:|
| id    | Unique identifier of your database | yes (but is automatic) | yes |
| name  | Name of database. | yes | no* |
| plan  | Which kind of plan your database is using | yes | no* |
| environment  | On which environment your database was created | yes | no* |
| project  | Project related with this database | no | no |
| quarantine_dt  | Date on which your database enter on quarantine | no | no |
| endpoint | Connection address for this database | no | yes |
| total_size_in_bytes  | Total size of your database. Depends of you plan | no | yes |
| used_size_in_bytes  | Used space of your database (this is not a realtime information) | no | yes |
| credentials  | List of credentials that have access to this database | no | yes |
\* This fields are not read only at creation time, but you can change it after.

### POST /api/database/
Create new database. Required fields are:

* name
* plan
* environment
* project, not required, but can be specified at creation time.


In response you will have the id and endpoint of your new database. By default, a new user with name 'u_`name of database`' will be create for this database.

#### Example

    curl -u admin:123456 -H 'content-type: application/json' http://localhost:8000/api/database/ -d '{ "name": "test database2", "plan": "/api/plan/1/", "environment": "/api/environment/1/" }'

Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/database/1/"
        }, 
        "id": 1, 
        "name": "test_database2", 
        "endpoint": "mongodb://<user>:<password>@127.0.0.1:27017/test_database2", 
        "plan": "http://localhost:8000/api/plan/1/", 
        "environment": "http://localhost:8000/api/environment/1/", 
        "project": null, 
        "quarantine_dt": null, 
        "total_size_in_bytes": 0, 
        "used_size_in_bytes": 16924, 
        "credentials": [
            "http://localhost:8000/api/credential/1/"
        ]
    }

### GET /api/database/
List all databases that you have permission.

#### Example

    curl -u admin:123456 http://localhost:8000/api/database/
Response:

    {
        "_links": {
            "count": 6, 
            "self": "http://localhost:8000/api/database/", 
            "previous": null, 
            "next": null
        }, 
        "database": [
            {
                "_links": {
                    "self": "http://localhost:8000/api/database/1/"
                }, 
                "id": 1, 
                "name": "my_first_database", 
                "endpoint": "mongodb://<user>:<password>@127.0.0.1:27017/my_first_database", 
                "plan": "http://localhost:8000/api/plan/1/", 
                "environment": "http://localhost:8000/api/environment/1/", 
                "project": null, 
                "quarantine_dt": null, 
                "total_size_in_bytes": 0, 
                "used_size_in_bytes": 17064, 
                "credentials": [
                    "http://localhost:8000/api/credential/1/", 
                    "http://localhost:8000/api/credential/7/"
                ]
            },
            ...
        ]
    }


### GET /api/database/*some_id*
Get data about one database.

#### Example

    curl -u admin:123456 http://localhost:8000/api/database/*some_id*/
Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/database/1/"
        }, 
        "id": 1, 
        "name": "test_database2", 
        "endpoint": "mongodb://<user>:<password>@127.0.0.1:27017/test_database2", 
        "plan": "http://localhost:8000/api/plan/1/", 
        "environment": "http://localhost:8000/api/environment/1/", 
        "project": null, 
        "quarantine_dt": null, 
        "total_size_in_bytes": 0, 
        "used_size_in_bytes": 16924, 
        "credentials": [
            "http://localhost:8000/api/credential/1/"
        ]
    }


### DELETE /api/database/*some_id*/
Put database on quarantine. If database is already on quarantine, it will be delete.
When database is no quarantine, all database credentials will be reseted to a unknow password, to avoid connections.

#### Example

    curl -u admin:123456 -X DELETE http://localhost:8000/api/database/1/


## Credential
Credential are the way you use to have access to some database. In DBaaS credentials are ALWAYS per database, since the engine allows you have the same user with access to more than one database. **Currently, you can't specify password, it's always generated by system.**

| Fields | Description | Required? | Read only? |
| ------ |:-------------:| -----:| -----:|
| id     | Unique identifier of your credential | yes (but its automatic) | yes |
| user   | user name of your credential | yes | yes |
| database  | database url (/api/database/*id*) | yes | yes |
| password | user password. Is hidden on list | no | no |

### GET /api/credential/
List all credentials. In list operation, passwords are not shown.

#### Example

    curl -u admin:123456 http://localhost:8000/api/credential/

Response:

    {
        "_links": {
            "count": 10, 
            "self": "http://localhost:8000/api/credential/", 
            "previous": null, 
            "next": null
        }, 
        "credential": [
            {
                "_links": {
                    "self": "http://localhost:8000/api/credential/1/"
                }, 
                "id": 1, 
                "user": "u_test_database2", 
                "database": "http://localhost:8000/api/database/1/"
            },
            ...
        ]
    }

### GET /api/credential/*some_id*
Get the password from credential.

#### Example

    curl -u admin:123456 http://localhost:8000/api/credential/1/

Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/credential/1/"
        }, 
        "id": 1, 
        "user": "u_test_database2", 
        "database": "http://localhost:8000/api/database/1/", 
        "password": "26WcA33q6F"
    }


### POST /api/credential/
Create new credential

   In response you will have the id and password of your new credential. Currently is not possible specify user password.

#### Example

    curl -u admin:123456 -H 'content-type: application/json' http://localhost:8000/api/credential/ -d '{ "user": "u_myusr1", "database": "/api/database/1/" }'

Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/credential/2/"
        }, 
        "id": 2, 
        "user": "u_myusr1", 
        "database": "http://localhost:8000/api/database/1/", 
        "password": "w9RXg222wK"
    }


### POST /api/credential/*some_id*/reset_password/
Generate a new password for your credential

#### Example

    curl -u admin:123456 -d '' http://localhost:8000/api/credential/1/reset_password/

Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/credential/1/"
        }, 
        "id": 1, 
        "user": "u_test_database2", 
        "database": "http://localhost:8000/api/database/1/", 
        "password": "PReduz6QtA"
    }

### DELETE /api/credential/*some_id*/
Remove credential.

#### Example

    curl -u admin:123456 -X DELETE http://localhost:8000/api/credential/1/

