from pymongo import MongoClient

client = MongoClient("mongodb://mongodb:27017")

db = client.admin

db.add_user('admin', '123456', roles=["userAdminAnyDatabase", "clusterAdmin", "readWriteAnyDatabase", "dbAdminAnyDatabase"])
