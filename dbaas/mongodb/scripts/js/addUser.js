db = db.getSisterDB(db_name);
db.addUser( { user: user_to_create,
              pwd: user_password,
              roles: [ "readWrite", "dbAdmin" ]
          } );