import logging
from base.engine import BaseEngine

LOG = logging.getLogger(__name__)


class MongoDB(BaseEngine):
    
    def url(self):
        return u"mongodb://%s:%s" % (self.instance.name, self.port)

    def status(self):
        raise NotImplementedError()

    def create_user(self, credential):
        self.run_mongo()

    def remove_user(self, credential):
        raise NotImplementedError()

    def create_database(self, database):
        raise NotImplementedError()

    def remove_database(self, database):
        raise NotImplementedError()

    def list_databases(self):
        """list databases in a instance"""
        raise NotImplementedError()

    def run_mongo(self, operation, objects):
        envs = {}
        for obj in objects:
            envs.update(self.to_envs(obj))
        self.call_script("./MongoManager.sh", envs=envs)

