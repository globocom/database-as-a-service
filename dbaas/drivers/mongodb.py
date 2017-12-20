# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import pymongo
from django.core.cache import cache
from contextlib import contextmanager
from . import BaseDriver
from . import DatabaseInfraStatus
from . import DatabaseStatus
from .errors import ConnectionError, AuthenticationError, \
    ReplicationNoPrimary, ReplicationNoInstances
from physical.models import Instance
from util import make_db_random_password
from system.models import Configuration
from dateutil import tz

LOG = logging.getLogger(__name__)

CLONE_DATABASE_SCRIPT_NAME = "mongodb_clone.sh"
MONGO_CONNECTION_DEFAULT_TIMEOUT = 5


class MongoDB(BaseDriver):

    default_port = 27017

    RESERVED_DATABASES_NAME = ['admin', 'config', 'local']

    def get_replica_name(self):
        """ Get replica name from databaseinfra. Use cache """
        if not self.databaseinfra.pk:
            # no cache when database infra is not persisted
            return self.__get_replica_name()

        key = 'mongo.replica.%d' % self.databaseinfra.pk
        repl_name = cache.get(key, None)
        if not repl_name:
            repl_name = self.__get_replica_name()
            cache.set(key, repl_name or '')
        return repl_name

    def __get_replica_name(self):
        """ Get replica name from mongodb """
        LOG.debug('Get replica name from %s', self.databaseinfra)
        repl_name = None
        try:
            with self.pymongo() as client:
                repl_status = client.admin.command('replSetGetStatus')
                repl_name = repl_status.get('set', None)
        except ConnectionError, pymongo.errors.OperationFailure:
            pass

        return repl_name

    def __concatenate_instances(self):
        return ",".join(["%s:%s" % (instance.address, instance.port)
                         for instance in self.databaseinfra.instances.filter(instance_type=Instance.MONGODB, is_active=True, read_only=False).all()])

    def __concatenate_instances_dns(self):
        return ",".join(
            ["%s:%s" % (instance.dns, instance.port)
                for instance in self.databaseinfra.instances.filter(instance_type=Instance.MONGODB, is_active=True, read_only=False).all() if not instance.dns.startswith('10.')]
        )

    def __concatenate_instances_dns_only(self):
        return ",".join(["%s" % (instance.dns)
                         for instance in self.databaseinfra.instances.filter(instance_type=Instance.MONGODB, is_active=True, read_only=False).all() if not instance.dns.startswith('10.')])

    def get_dns_port(self):
        port = self.databaseinfra.instances.filter(
            instance_type=Instance.MONGODB, is_active=True).all()[0].port
        dns = self.__concatenate_instances_dns_only()
        return dns, port

    def get_connection(self, database=None):
        uri = "mongodb://<user>:<password>@%s" % self.__concatenate_instances()
        if database:
            uri = "%s/%s" % (uri, database.name)

        if (len(self.databaseinfra.instances.all()) > 1):
            repl_name = self.get_replica_name()
            if repl_name:
                uri = "%s?replicaSet=%s" % (uri, repl_name)

        return uri

    def get_admin_connection(self,):
        if self.databaseinfra.engine.version >= '3.4.0':
            uri = "mongodb://{user}:{password}@{instances}/admin".format(
                user=self.databaseinfra.user,
                password=self.databaseinfra.password,
                instances=self.__concatenate_instances()
            )

            if (len(self.databaseinfra.instances.all()) > 1):
                repl_name = self.get_replica_name()
                if repl_name:
                    uri = "%s?replicaSet=%s" % (uri, repl_name)
        else:
            uri = "{instances}".format(instances=self.__concatenate_instances())

            if (len(self.databaseinfra.instances.all()) > 1):
                repl_name = self.get_replica_name()
                if repl_name:
                    uri = "{repl_name}/{uri}".format(
                        repl_name=repl_name, uri=uri)
            uri = " {uri} admin -u{user} -p{password}".format(
                uri=uri,
                user=self.databaseinfra.user,
                password=self.databaseinfra.password
            )

        return uri

    def get_connection_dns(self, database=None):
        uri = "mongodb://<user>:<password>@%s" % self.__concatenate_instances_dns()
        if database:
            uri = "%s/%s" % (uri, database.name)

        if (len(self.databaseinfra.instances.all()) > 1):
            repl_name = self.get_replica_name()
            if repl_name:
                uri = "%s?replicaSet=%s" % (uri, repl_name)

        return uri

    def __get_admin_connection(self, instance=None):
        if instance:
            return "mongodb://%s:%s" % (instance.address, instance.port)
        return "mongodb://%s" % self.__concatenate_instances()

    def __mongo_client__(self, instance):
        connection_address = self.__get_admin_connection(instance)
        if not self.databaseinfra and instance:
            self.databaseinfra = instance.databaseinfra
        try:
            # mongo uses timeout in mili seconds
            connection_timeout_in_miliseconds = Configuration.get_by_name_as_int(
                'mongo_connect_timeout', default=MONGO_CONNECTION_DEFAULT_TIMEOUT) * 1000

            client = pymongo.MongoClient(
                connection_address, connectTimeoutMS=connection_timeout_in_miliseconds)
            if (not instance) or (instance and instance.instance_type != instance.MONGODB_ARBITER):
                if self.databaseinfra.user and self.databaseinfra.password:
                    LOG.debug('Authenticating databaseinfra %s',
                              self.databaseinfra)
                    client.admin.authenticate(self.databaseinfra.user,
                                              self.databaseinfra.password)
            return client
        except TypeError:
            raise AuthenticationError(
                message='Invalid address: ' % connection_address)

    def get_client(self, instance):
        return self.__mongo_client__(instance)

    def lock_database(self, client):
        client.fsync(lock=True)

    def unlock_database(self, client):
        client.unlock()

    @contextmanager
    def pymongo(self, instance=None, database=None):
        client = None
        try:
            client = self.__mongo_client__(instance)

            if database is None:
                return_value = client
            else:
                return_value = getattr(client, database.name)
            yield return_value
        except pymongo.errors.OperationFailure, e:
            if e.code == 18:
                raise AuthenticationError('Invalid credentials to databaseinfra %s: %s' %
                                          (self.databaseinfra, self.__get_admin_connection()))
            raise ConnectionError('Error connecting to databaseinfra %s (%s): %s' %
                                  (self.databaseinfra, self.__get_admin_connection(), e.message))
        except pymongo.errors.PyMongoError, e:
            raise ConnectionError('Error connecting to databaseinfra %s (%s): %s' %
                                  (self.databaseinfra, self.__get_admin_connection(), e.message))
        finally:
            try:
                if client:
                    client.close()
            except:
                LOG.warn('Error disconnecting from databaseinfra %s. Ignoring...',
                         self.databaseinfra, exc_info=True)

    def check_status(self, instance=None):
        with self.pymongo(instance=instance) as client:
            try:
                ok = client.admin.command('ping')
                return True
            except pymongo.errors.PyMongoError, e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, e.message))

            if isinstance(ok, dict) and ok.get('ok', 0) != 1.0:
                raise ConnectionError(
                    'Invalid status for ping command to databaseinfra %s' % self.databaseinfra)

    def list_databases(self, instance=None):
        dbs_names = []
        with self.pymongo(instance=instance) as client:
            try:
                list_of_dbs = client.admin.command('listDatabases')
                for db in list_of_dbs['databases']:
                    dbs_names.append(db['name'])
                return dbs_names
            except pymongo.errors.PyMongoError, e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, e.message))

    def get_total_size_from_instance(self, instance):
        return (self.databaseinfra.disk_offering.size_bytes()
                if self.databaseinfra.disk_offering else 0.0)

    def get_used_size_from_instance(self, instance):
        with self.pymongo(instance=instance) as client:
            database_info = client.admin.command('listDatabases')
            return database_info.get(
                'totalSize', 0
            )

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra)

        with self.pymongo() as client:
            json_server_info = client.server_info()
            json_list_databases = client.admin.command('listDatabases')

            databaseinfra_status.version = json_server_info.get(
                'version', None)
            databaseinfra_status.used_size_in_bytes = json_list_databases.get(
                'totalSize', 0)

            list_databases = self.list_databases()
            for database in self.databaseinfra.databases.all():
                database_name = database.name
                json_db_status = getattr(
                    client, database_name).command('dbStats')
                db_status = DatabaseStatus(database)
                # is_alive?
                try:
                    if self.check_status() and (database_name in list_databases):
                        db_status.is_alive = True
                except:
                    pass

                storageSize = json_db_status.get("storageSize") or 0
                db_status.used_size_in_bytes = storageSize
                db_status.total_size_in_bytes = json_db_status.get(
                    "fileSize") or 0
                databaseinfra_status.databases_status[
                    database_name] = db_status

        return databaseinfra_status

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.add_user(
                credential.user, password=credential.password, roles=roles)

    def update_user(self, credential):
        self.create_user(credential)

    def remove_user(self, credential):
        with self.pymongo(database=credential.database) as mongo_database:
            mongo_database.remove_user(credential.user)

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        with self.pymongo(database=database) as mongo_database:
            mongo_database.create_collection('dbaas.dummy')

    def remove_database(self, database):
        LOG.info("removing database %s" % database.name)
        with self.pymongo() as client:
            client.drop_database(database.name)

    def change_default_pwd(self, instance):
        with self.pymongo(instance=instance) as client:
            new_password = make_db_random_password()
            client.admin.add_user(
                name=instance.databaseinfra.user, password=new_password)
            return new_password

    def clone(self):
        return CLONE_DATABASE_SCRIPT_NAME

    def check_instance_is_eligible_for_backup(self, instance):
        if instance.instance_type == instance.MONGODB_ARBITER:
            return False

        if self.databaseinfra.instances.count() == 1:
            return True

        with self.pymongo(instance=instance) as client:
            try:
                ismaster = client.admin.command('isMaster')
                if ismaster['ismaster']:
                    return False
                else:
                    return True

            except pymongo.errors.PyMongoError, e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, e.message))

    def check_instance_is_master(self, instance):
        if instance.instance_type == instance.MONGODB_ARBITER:
            return False

        if self.databaseinfra.instances.count() == 1:
            return True

        with self.pymongo(instance=instance) as client:
            try:
                ismaster = client.admin.command('isMaster')
                if ismaster['ismaster']:
                    return True
                else:
                    return False

            except pymongo.errors.PyMongoError, e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, e.message))

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance):
            return 0

        instance_opttime = None
        instance_member = None
        with self.pymongo() as client:
            replSetGetStatus = client.admin.command('replSetGetStatus')
            primary_opttime = None
            for member in replSetGetStatus['members']:
                if member['stateStr'] == 'PRIMARY':
                    primary_opttime = member['optimeDate'].replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())

            if primary_opttime is None:
                raise ReplicationNoPrimary("There is not any Primary in the Replica Set")

            for member in replSetGetStatus['members']:
                if member["name"] == "{}:{}".format(instance.address, instance.port):
                    instance_opttime = member['optimeDate'].replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
                    instance_member = member

        if instance_opttime is None:
            raise ReplicationNoInstances("Could not find the instance in the Replica Set")

        delay = primary_opttime - instance_opttime
        seconds_delay = delay.days * 24 * 3600 + delay.seconds
        LOG.info("The instance {} is {} seconds behind Primary".format(instance, seconds_delay))

        if seconds_delay == 0 and instance_member["stateStr"] not in ["PRIMARY", "SECONDARY"]:
            LOG.info("The instance {} is 0 seconds behind Primary, but it is not Secondary. It is {}".format(instance, instance_member["stateStr"]))
            return 100000

        return seconds_delay

    def get_max_replica_id(self, ):
        with self.pymongo() as client:
            replSetGetStatus = client.admin.command('replSetGetStatus')
            max_id = 0
            for member in replSetGetStatus['members']:
                repl_id = member["_id"]
                if repl_id > max_id:
                    max_id = repl_id
            return max_id

    def is_replication_ok(self, instance):
        if self.check_instance_is_master(instance=instance):
            return True

        if self.get_replication_info(instance=instance) <= 2:
            return True

        return False

    def initialization_script_path(self, host=None):
        return "/etc/init.d/mongodb {option}"

    def deprecated_files(self,):
        return ['mongod.lock', 'mongod.running']

    def data_dir(self, ):
        return '/data/data/'

    def switch_master(self, instance=None):
        client = self.get_client(None)
        try:
            client.admin.command('replSetStepDown', 10)
        except pymongo.errors.AutoReconnect:
            pass

    def get_database_agents(self):
        return []

    def get_default_database_port(self):
        return 27017

    def get_default_instance_type(self):
        return Instance.MONGODB

    @property
    def database_key(self):
        return None

    @property
    def replica_set_name(self):
        return 'ReplicaSet_{}'.format(self.databaseinfra.name)

    def get_configuration(self):
        with self.pymongo() as client:
            configuration = client.admin.command({'getParameter': '*'})

            if 'quiet' in configuration:
                configuration['quiet'] = str(configuration['quiet']).lower()

            wiredTyger_cache = self.get_wiredTiger_engineConfig_cacheSizeGB()
            if wiredTyger_cache:
                configuration.update({'wiredTiger_engineConfig_cacheSizeGB': wiredTyger_cache})

            return configuration

    def get_oplogsize(self):
        return None

    def get_wiredTiger_engineConfig_cacheSizeGB(self):
        with self.pymongo() as client:
            serverStatus = client.admin.command("serverStatus")
            try:
                max_cache_bytes = serverStatus['wiredTiger']['cache']["maximum bytes configured"]
            except KeyError:
                return None
            return round(max_cache_bytes / 1024.0 / 1024.0 / 1024.0, 2)

    def set_configuration(self, instance, name, value):
        client = self.get_client(instance)

        if name == 'quiet':
            if value == 'true':
                update_value = True
            elif value == 'false':
                update_value = False
            else:
                error = 'BadValue quiet: {}. Must be true or false.'.format(value)
                raise ValueError(error)
            client.admin.command('setParameter', 1, quiet=update_value)

        elif name == 'logLevel':
            client.admin.command('setParameter', 1, logLevel=int(value))

        elif name == 'wiredTiger_engineConfig_cacheSizeGB':
            cache = "cache_size={}".format(int(float(value) * 1024 * 1024 * 1024))
            client.admin.command('setParameter', 1, wiredTigerEngineRuntimeConfig=cache)

        else:
            raise Exception("Could not set configuration for {}. It's unknown.".format(name))

    def get_database_process_name(self):
        return "mongod"

    def initialization_parameters(self, instance):
        database_rule = 'SECONDARY'
        if instance.instance_type == instance.MONGODB_ARBITER:
            database_rule = 'ARBITER'

        return {
            'DATABASERULE': database_rule
        }

    def configuration_parameters(self, instance):
        config = {}
        config.update(self.initialization_parameters(instance))
        config['REPLICASETNAME'] = self.get_replica_name()
        config['MONGODBKEY'] = instance.databaseinfra.database_key
        return config

    def configuration_parameters_for_log_resize(self, instance):
        return {
            'DRIVER_NAME': 'mongodb_single',
            'PORT': 27018
        }

    @classmethod
    def topology_name(cls):
        return ['mongodb_single']


class MongoDBReplicaSet(MongoDB):

    @property
    def database_key(self):
        from util import get_mongodb_key_file
        return get_mongodb_key_file(self.databaseinfra)

    def get_configuration(self):
        configuration = super(MongoDBReplicaSet, self).get_configuration()
        configuration['oplogSize'] = self.get_oplogsize()
        return configuration

    def get_oplogsize(self):
        with self.pymongo() as client:
            # firstc = client["local"]["oplog.rs"].find().sort("$natural", pymongo.ASCENDING).limit(1)[0]
            # lastc = client["local"]["oplog.rs"].find().sort("$natural", pymongo.DESCENDING).limit(1)[0]
            oplog_stats = client["local"].command("collStats", "oplog.rs")
            if 'maxSize' in oplog_stats:
                logSize = oplog_stats['maxSize']
            else:
                oplogc = client["local"]["system.namespaces"].find_one({
                    'name': "local.oplog.rs"
                })
                logSize = oplogc["options"]["size"]

        return logSize / 1024 / 1024

    @classmethod
    def topology_name(cls):
        return ['mongodb_replica_set']
