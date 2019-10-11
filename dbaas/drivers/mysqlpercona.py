from . import mysqldb
from physical.models import Instance


class MySQLPercona(mysqldb.MySQL):

    def get_default_instance_type(self):
        return Instance.MYSQL_PERCONA

    @classmethod
    def topology_name(cls):
        return ['mysql_percona_single']


class MySQLPerconaFOXHA(mysqldb.MySQLFOXHA):

    def get_default_instance_type(self):
        return Instance.MYSQL_PERCONA

    @classmethod
    def topology_name(cls):
        return ['mysql_percona_foxha']
