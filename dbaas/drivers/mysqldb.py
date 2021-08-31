# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import logging
import _mysql as mysqldb
import _mysql_exceptions
from contextlib import contextmanager
from dbaas_credentials.models import CredentialType
from util import make_db_random_password, get_credentials_for
from logical.models import Credential
from system.models import Configuration
from physical.models import Instance
from drivers import BaseDriver, DatabaseInfraStatus, DatabaseStatus
from drivers import errors as driver_errors


LOG = logging.getLogger(__name__)

ER_DB_CREATE_EXISTS = 1007
ER_DB_DROP_EXISTS = 1008
ER_ACCESS_DENIED_ERROR = 1045
ER_CANNOT_USER = 1396
ER_WRONG_STRING_LENGTH = 1470
ER_CAN_NOT_CONNECT = 2003
LOST_CONNECTION = 2013

CLONE_DATABASE_SCRIPT_NAME = "mysql_clone.sh"
MYSQL_CONNECTION_DEFAULT_TIMEOUT = 5


class MySQL(BaseDriver):

    default_port = 3306
    RESERVED_DATABASES_NAME = ['admin', 'test', 'mysql', 'information_schema']

    USER_ROLES = {
        Credential.OWNER: ["ALL PRIVILEGES"],
        Credential.READ_WRITE: [
            "SELECT", "EXECUTE", "UPDATE", "DELETE", "INSERT"
        ],
        Credential.READ_ONLY: ["SELECT", "EXECUTE"]
    }

    @property
    def ports(self):
        return (3306,)

    @property
    def set_require_ssl_for_users(self):
        return True

    def get_connection(self, database=None):
        # my_instance = self.databaseinfra.instances.all()[0]
        uri = "mysql://<user>:<password>@%s" % (self.databaseinfra.endpoint)
        if database:
            uri = "%s/%s" % (uri, database.name)
        return uri

    def get_connection_dns(self, database=None):
        # my_instance = self.databaseinfra.instances.all()[0]
        uri = "mysql://<user>:<password>@%s" % (
            self.databaseinfra.endpoint_dns)
        if database:
            uri = "%s/%s" % (uri, database.name)
        return uri

    def get_dns_port(self, instance=None):
        """
        endpoint is on the form HOST:PORT
        """
        if instance:
            return instance.address, instance.port

        endpoint = self.databaseinfra.endpoint_dns.split(':')
        return endpoint[0], int(endpoint[1])

    def get_master_instance(self, ignore_instance=None, default_timeout=False):
        instances = self.get_database_instances()
        if ignore_instance:
            instances.remove(ignore_instance)
        for instance in instances:
            try:
                if self.check_instance_is_master(instance):
                    return instance
            except driver_errors.ConnectionError:
                continue

        return None

    def get_master_instance2(self, ignore_instance=None, default_timeout=False):
        return self.get_master_instance(ignore_instance,default_timeout )

    def __get_admin_connection(self, instance=None):
        """
        endpoint is on the form HOST:PORT
        """
        if instance:
            return instance.address, instance.port

        endpoint = self.databaseinfra.endpoint.split(':')
        return endpoint[0], int(endpoint[1])

    def __mysql_client__(self, instance, database='mysql',
                         default_timeout=False):
        connection_address, connection_port = self.__get_admin_connection(
            instance)
        try:
            LOG.debug(
                'Connecting to mysql databaseinfra %s', self.databaseinfra)
            # mysql uses timeout in seconds
            if default_timeout:
                connection_timeout_in_seconds = (
                    MYSQL_CONNECTION_DEFAULT_TIMEOUT
                )
            else:
                connection_timeout_in_seconds = (
                    Configuration.get_by_name_as_int(
                        'mysql_connect_timeout',
                        default=MYSQL_CONNECTION_DEFAULT_TIMEOUT
                    )
                )

            client = mysqldb.connect(
                host=connection_address,
                port=int(connection_port),
                user=self.databaseinfra.user,
                passwd=self.databaseinfra.password,
                db=database,
                connect_timeout=connection_timeout_in_seconds
            )
            LOG.debug(
                'Successfully connected to mysql databaseinfra %s' % (
                    self.databaseinfra)
                )
            return client
        except Exception as e:
            raise e

    def get_client(self, instance):
        return self.__mysql_client__(instance)

    def lock_database(self, client):
        client.query("SET session lock_wait_timeout = 60")
        client.query("flush tables with read lock")
        client.query("flush logs")

    def unlock_database(self, client):
        client.query("unlock tables")

    @contextmanager
    def mysqldb(self, instance=None, database=None):
        client = None
        try:
            yield self.__mysql_client__(instance)
        except _mysql_exceptions.OperationalError as e:
            if e.args[0] == ER_ACCESS_DENIED_ERROR:
                raise driver_errors.AuthenticationError(e.args[1])
            elif e.args[0] == ER_CAN_NOT_CONNECT:
                raise driver_errors.ConnectionError(e.args[1])
            elif e.args[0] == LOST_CONNECTION:
                raise driver_errors.ConnectionError(e.args[1])
            else:
                raise driver_errors.GenericDriverError(e.args)
        finally:
            try:
                if client:
                    LOG.debug(
                        'Disconnecting mysql databaseinfra %s',
                        self.databaseinfra
                    )
                    client.close()
            except Exception:
                LOG.warn(
                    'Error disconnecting from databaseinfra %s. Ignoring...',
                    self.databaseinfra,
                    exc_info=True
                )

    def __query(self, query_string, instance=None):
        with self.mysqldb(instance=instance) as client:
            try:
                LOG.debug("query_string: %s" % query_string)
                client.query(query_string)
                r = client.store_result()
                if r is not None:
                    return r.fetch_row(maxrows=0, how=1)
            except _mysql_exceptions.ProgrammingError as e:
                LOG.error("__query ProgrammingError: %s" % e)
                if e.args[0] == ER_DB_CREATE_EXISTS:
                    raise driver_errors.DatabaseAlreadyExists(e.args[1])
                else:
                    raise driver_errors.GenericDriverError(e.args)
            except _mysql_exceptions.OperationalError as e:
                LOG.error("__query OperationalError: %s" % e)
                if e.args[0] == ER_DB_DROP_EXISTS:
                    raise driver_errors.DatabaseDoesNotExist(e.args[1])
                elif e.args[0] == ER_CANNOT_USER:
                    raise driver_errors.InvalidCredential(e.args[1])
                elif e.args[0] == ER_WRONG_STRING_LENGTH:
                    raise driver_errors.InvalidCredential(e.args[1])
                else:
                    raise driver_errors.GenericDriverError(e.args)
            except Exception as e:
                raise driver_errors.GenericDriverError(e.args)

    def query(self, query_string, instance=None):
        return self.__query(query_string, instance)

    def get_total_size_from_instance(self, instance):
        return (self.databaseinfra.disk_offering.size_bytes()
                if self.databaseinfra.disk_offering else 0.0)

    def get_used_size_from_instance(self, instance):
        db_sizes = self.query("SELECT s.schema_name 'Database', ifnull(SUM( t.data_length + t.index_length), 0) 'Size' \
                                FROM information_schema.SCHEMATA s \
                                left outer join information_schema.TABLES t on s.schema_name = t.table_schema \
                                GROUP BY s.schema_name", instance=instance)
        return sum(
            map(
                lambda d: float(d.get('Size', 0)),
                db_sizes
            )
        )

    def info(self):
        from logical.models import Database

        databaseinfra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra)

        r = self.__query("SELECT VERSION()")
        databaseinfra_status.version = r[0]['VERSION()']

        db_sizes = self.__query("SELECT s.schema_name 'Database', ifnull(SUM( t.data_length + t.index_length), 0) 'Size' \
                                FROM information_schema.SCHEMATA s \
                                  left outer join information_schema.TABLES t on s.schema_name = t.table_schema \
                                GROUP BY s.schema_name")

        all_dbs = {}
        for database in db_sizes:
            all_dbs[database['Database']] = int(database['Size'])

        list_databases = self.list_databases()
        for database_name in all_dbs.keys():
            database_model = None
            try:
                # LOG.debug("checking status for database %s" % database_name)
                database_model = Database.objects.get(
                    name=database_name, databaseinfra=self.databaseinfra)
            except Database.DoesNotExist:
                pass

            if database_model:
                db_status = DatabaseStatus(database_model)
                # is_alive?
                try:
                    if self.check_status() and (database_name in list_databases):
                        db_status.is_alive = True
                except Exception as e:
                    LOG.warning(
                        "could not retrieve db status for %s: %s" % (
                            database_name, e)
                        )

                db_status.total_size_in_bytes = 0
                db_status.used_size_in_bytes = all_dbs[database_name]

                databaseinfra_status.databases_status[
                    database_name] = db_status

        databaseinfra_status.used_size_in_bytes = sum(all_dbs.values())

        return databaseinfra_status

    def check_status(self, instance=None):
        status = False
        try:
            result = self.__query("SELECT 1", instance=instance)
            if result[0]['1'] == '1':
                status = True
        except Exception as e:
            LOG.warning(
                "could not retrieve status for instance %s: %s" % (
                    instance, e)
                )

        return status

    def create_database(self, database):
        LOG.info("creating database %s" % database.name)
        self.__query("CREATE DATABASE %s" % database.name)

    def create_user(self, credential):
        LOG.info("creating user {} to {}".format(
            credential.user, credential.database))

        if credential.user in self.list_users():
            raise driver_errors.CredentialAlreadyExists()
        query = "CREATE USER '{}'@'%' IDENTIFIED BY '{}'".format(
            credential.user, credential.password)
        self.__query(query)

        query = "GRANT {} ON {}.* TO '{}'@'%'".format(
            ','.join(self.USER_ROLES[credential.privileges]),
                credential.database, credential.user
            )
        self.__query(query)

        if credential.force_ssl:
            self.set_user_require_ssl(credential)

    def remove_database(self, database):
        LOG.info("removing database %s" % (database.name))
        self.__query("DROP DATABASE %s" % database.name)

    def list_databases(self, instance=None):
        """list databases in a databaseinfra"""
        LOG.info("listing databases in %s" % (self.databaseinfra))
        results = self.__query("SHOW databases", instance=instance)
        return [result["Database"] for result in results]

    def disconnect_user(self, credential):
        # It works only in mysql >= 5.5
        r = self.__query("SELECT id FROM information_schema.processlist WHERE user='%s' AND db='%s'" %
                         (credential.user, credential.database))
        for session in r:
            LOG.info("disconnecting user %s from database %s id_session %s" %
                     (credential.user, credential.database, session['id']))
            self.__query("KILL CONNECTION %s" % session['id'])

    def remove_user(self, credential):
        LOG.info("removing user %s from %s" %
                 (credential.user, credential.database))
        self.disconnect_user(credential)
        self.__query("DROP USER '%s'@'%%'" % credential.user)

    def update_user(self, credential):
        self.remove_user(credential)
        self.create_user(credential)

    def list_users(self, instance=None):
        LOG.info("listing users in %s" % (self.databaseinfra))
        results = self.__query(
            "SELECT distinct User FROM mysql.user where User != ''",
            instance=instance
        )
        return [result["User"] for result in results]

    def change_default_pwd(self, instance):
        new_password = make_db_random_password()
        self.__query("SET PASSWORD FOR '%s'@'%%' = PASSWORD('%s')" (
            instance.databaseinfra.user, new_password))
        return new_password

    def clone(self):
        return CLONE_DATABASE_SCRIPT_NAME

    def check_instance_is_eligible_for_backup(self, instance):
        if not instance.is_active:
            return False
        if self.databaseinfra.instances.filter(is_active=True).count() == 1:
            return True
        results = self.__query(
            query_string="show variables like 'read_only'", instance=instance)
        if results[0]["Value"] == "ON":
            return True
        else:
            return False

    def check_instance_is_master(self, instance, default_timeout=False):
        if not instance.is_active:
            return False
        return self.replication_topology_driver.check_instance_is_master(
            driver=self, instance=instance
        )

    def set_master(self, instance):
        return self.replication_topology_driver.set_master(
            driver=self, instance=instance
        )

    def set_read_ip(self, instance):
        return self.replication_topology_driver.set_read_ip(
            driver=self, instance=instance
        )

    def get_replication_info(self, instance):
        results = self.__query(
            query_string="show slave status", instance=instance
        )

        seconds_behind_master = results[0]['Seconds_Behind_Master']
        if seconds_behind_master is None:
            raise driver_errors.ReplicationNotRunningError
        return int(seconds_behind_master)

    def get_heartbeat_replication_info(self, instance):
        results = self.__query(
            query_string=("select DATE_FORMAT(ts, '%Y-%m-%d %H:%i:%s') ts, "
                          "DATE_FORMAT(now(), '%Y-%m-%d %H:%i:%s') now "
                          "from heartbeat.heartbeat"),
            instance=instance)
        now = datetime.datetime.strptime(
            results[0]['now'], '%Y-%m-%d %H:%M:%S'
        )
        ts = datetime.datetime.strptime(results[0]['ts'], '%Y-%m-%d %H:%M:%S')
        datediff = now - ts
        return datediff.seconds

    def is_replication_ok(self, instance):
        if self.get_replication_info(instance=instance) == 0:
            return True

        return False

    def is_heartbeat_replication_ok(self, instance):
        if self.get_heartbeat_replication_info(instance=instance) == 0:
            return True

        return False

    def deprecated_files(self,):
        return ['*.pid', "*.err", "auto.cnf"]

    def data_dir(self, ):
        return '/data/data/'

    def switch_master(self, instance=None, preferred_slave_instance=None):
        return self.replication_topology_driver.switch_master(driver=self)

    def start_slave(self, instance):
        client = self.get_client(instance)
        client.query("start slave")

    def stop_slave(self, instance):
        client = self.get_client(instance)
        client.query("stop slave")

    def get_database_agents(self):
        return self.replication_topology_driver.get_database_agents()

    def get_default_database_port(self):
        return 3306

    def get_default_instance_type(self):
        return Instance.MYSQL

    def get_configuration(self):
        configurations = {}

        results = self.__query("SHOW VARIABLES")
        for result in results:
            configurations[result['Variable_name']] = result['Value']

        return configurations

    def set_configuration(self, instance, name, value):
        client = self.get_client(instance)
        value = value.strip("'\"")
        if value == '':
            query = "set global {} = ''".format(name)
        if name == 'init_connect':
            query = 'set global {} = "{}"'.format(name, value)
        if name == 'audit_log_exclude_accounts':
            query = 'set global {} = "{}"'.format(name, value)
        elif name == 'sql_mode' and value.lower() != 'default':
            query = "set global {} = '{}'".format(name, value)
        else:
            query = "set global {} = {}".format(name, value)
        client.query(query)

    def get_database_process_name(self):
        return "mysqld"

    def initialization_parameters(self, instance):
        return self.parameters_mysql(instance)

    def configuration_parameters(self, instance, **kw):
        config = self.parameters_mysql(instance)
        config.update(kw)
        return config

    def parameters_mysql(self, instance):
        return {
            'SERVERID': int(instance.dns.split('-')[1])
        }

    @classmethod
    def topology_name(cls):
        return ['mysql_single']

    @property
    def credential_type(self):
        return CredentialType.MYSQL

    def build_new_infra_auth(self):
        credential = get_credentials_for(
            environment=self.databaseinfra.environment,
            credential_type=self.credential_type
        )
        return credential.user, credential.password, ''

    def set_user_require_ssl(self, credential):
        LOG.info("settint user {} to require SSL".format(credential.user))

        if credential.user not in self.list_users():
            raise driver_errors.CredentialDoesNotExists()

        query = "GRANT USAGE ON *.* TO '{}'@'%' REQUIRE SSL".format(
            credential.user)

        self.__query(query)

    def set_user_not_require_ssl(self, credential):
        LOG.info("settint user {} to NOT require SSL".format(credential.user))

        if credential.user not in self.list_users():
            raise driver_errors.CredentialDoesNotExists()

        query = "GRANT USAGE ON *.* TO '{}'@'%' REQUIRE NONE".format(
            credential.user)

        self.__query(query)

    def create_metric_collector_user(self, username, password):
        host = '127.0.0.1'
        grants = "SELECT, PROCESS, REPLICATION CLIENT, SHOW VIEW"
        query = "GRANT {} ON *.* TO '{}'@'{}' IDENTIFIED BY '{}'".format(
            grants, username, host, password)
        self.__query(query)

    def remove_metric_collector_user(self, username):
        host = '127.0.0.1'
        drop_user_cmd = "DROP USER '{}'@'{}'".format(username, host)
        self.__query(drop_user_cmd)

    def get_start_pty_default(self):
        return True


class MySQLFOXHA(MySQL):

    @classmethod
    def topology_name(cls):
        return ['mysql_foxha']

    def start_replication_parameters(self, instance):
        base = self.initialization_parameters(instance)

        replica_credential = get_credentials_for(
            self.databaseinfra.environment, CredentialType.MYSQL_REPLICA
        )
        base['REPLICA_USER'] = replica_credential.user
        base['REPLICA_PASSWORD'] = replica_credential.password

        hosts = set(self.databaseinfra.hosts)
        hosts.discard(instance.hostname)
        base['IPMASTER'] = hosts.pop().address
        base['HEARTBEAT_START_COMMAND'] = instance.hostname.commands.heartbeat(
            action='start'
        )

        return base

    def set_replication_user_require_ssl(self, instance=None):
        LOG.info("settint replication user to require SSL")

        replica_credential = get_credentials_for(
            self.databaseinfra.environment, CredentialType.MYSQL_REPLICA
        )

        query = "GRANT USAGE ON *.* TO '{}'@'%' REQUIRE SSL".format(
            replica_credential.user)

        self.query(query, instance)

    def set_replication_user_not_require_ssl(self, instance=None):
        LOG.info("settint replication user to NOT require SSL")

        replica_credential = get_credentials_for(
            self.databaseinfra.environment, CredentialType.MYSQL_REPLICA
        )

        query = "GRANT USAGE ON *.* TO '{}'@'%' REQUIRE NONE".format(
            replica_credential.user)

        self.query(query, instance)

    def set_replication_require_ssl(self, instance=None, ca_path=None):
        LOG.info("settint replication to require SSL")

        query = "stop slave;"
        self.query(query, instance)

        query = "CHANGE MASTER TO MASTER_SSL=1, MASTER_SSL_CA = '{}'"
        query = query.format(ca_path)
        self.query(query, instance)

        query = "start slave;"
        self.query(query, instance)

    def set_replication_not_require_ssl(self, instance=None, ca_path=None):
        LOG.info("settint replication to NOT require SSL")

        query = "stop slave;"
        self.query(query, instance)

        query = "CHANGE MASTER TO MASTER_SSL=0, MASTER_SSL_CA = ''"
        query = query.format(ca_path)
        self.query(query, instance)

        query = "start slave;"
        self.query(query, instance)
