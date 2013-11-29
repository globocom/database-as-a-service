The API allows you to maintain yours databases.

## Getting Started

I assumed I know about [REST API](http://en.wikipedia.org/wiki/Representational_state_transfer) and [JSON](http://en.wikipedia.org/wiki/JSON). But if you don't know, don't worry about because I give you examples using `curl`.

To ensure you will be able to run all examples, they are based on sample data provided by `make reset_data` command. So, 

* [Database](#database)
   * [Create new database](#create-new-database)
   * [List all databases](#list-all-databases)
* [Credential](#credential)
   * [Create new credential](#create-new-credential)<br>

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

    curl -u USER:PASS -H 'content-type: application/json' http://localhost:8000/api/database/ -d '{ "name": "test database2", "plan": "/api/plan/1/", "environment": "/api/environment/1/" }'

Response:

    {
        "_links": {
            "self": "http://localhost:8000/api/database/16/"
        }, 
        "id": 16, 
        "name": "test_database2", 
        "endpoint": "mongodb://<user>:<password>@127.0.0.1:27017/test_database2", 
        "plan": "http://localhost:8000/api/plan/1/", 
        "environment": "http://localhost:8000/api/environment/1/", 
        "project": null, 
        "quarantine_dt": null, 
        "total_size_in_bytes": 0, 
        "used_size_in_bytes": 16932, 
        "credentials": [
            "http://localhost:8000/api/credential/9/"
        ]
    }

## GET /api/database/
List all databases that you have permission.

#### Example

    curl -u USER:PASS http://localhost:8000/api/database/
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


## Credential

### Functions

## POST /api/credential/
Create new credential

| Parameter | Description | Required? |
| ---- |:-------------:| -----:|
| user  | user name of your credential | yes |
| database  | database url | yes |

   In response you will have the id and password of your new credential. At this time, is not possible specify user password.

#### Example

    curl -u USER:PASS -H 'content-type: application/json' http://localhost:8000/api/credential/ -d '
    { "user": "u_myusr1", "database": "/api/database/1/" }'
