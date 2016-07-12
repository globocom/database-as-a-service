# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import redis
from redis.sentinel import Sentinel
from contextlib import contextmanager
from . import BaseDriver
from . import DatabaseInfraStatus
from . import DatabaseStatus
from . import ConnectionError
from system.models import Configuration
from physical.models import Instance
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr

LOG = logging.getLogger(__name__)

CLONE_DATABASE_SCRIPT_NAME = "redis_clone.py"
REDIS_CONNECTION_DEFAULT_TIMEOUT = 5


class Redis(BaseDriver):

    default_port = 6379

    def __concatenate_instances(self):
        if self.databaseinfra.plan.is_ha:
            return ",".join(["%s:%s" % (instance.address, instance.port)
                             for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS_SENTINEL, is_active=True).all()])
        else:
            return ",".join(["%s:%s" % (instance.address, instance.port)
                             for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS, is_active=True).all()])

    def __concatenate_instances_dns(self):
        if self.databaseinfra.plan.is_ha:
            return ",".join(["%s:%s" % (instance.dns, instance.port)
                             for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS_SENTINEL, is_active=True).all() if not instance.dns.startswith('10.')])
        else:
            return ",".join(["%s:%s" % (instance.dns, instance.port)
                             for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS, is_active=True).all() if not instance.dns.startswith('10.')])

    def get_connection(self, database=None):
        if self.databaseinfra.plan.is_ha:
            uri_instance_type = 'sentinel'
            database_name = 'service_name:%s' % (self.databaseinfra.name)
        else:
            uri_instance_type = 'redis'
            database_name = '0'
        uri = "%s://:<password>@%s/%s" % (uri_instance_type,
                                          self.__concatenate_instances(), database_name)
        return uri

    def get_connection_dns(self, database=None):
        if self.databaseinfra.plan.is_ha:
            uri_instance_type = 'sentinel'
            database_name = 'service_name:%s' % (self.databaseinfra.name)
        else:
            uri_instance_type = 'redis'
            database_name = '0'
        uri = "%s://:<password>@%s/%s" % (uri_instance_type,
                                          self.__concatenate_instances_dns(), database_name)
        return uri

    def get_connection_dns_simple(self, database=None):
        if self.databaseinfra.plan.is_ha:
            uri_instance_type = 'sentinel'
            #database_name = 'service_name:%s' % (self.databaseinfra.name)
        else:
            uri_instance_type = 'redis'
            database_name = '0'
        uri = "%s://%s" % (uri_instance_type,
                                          self.__concatenate_instances_dns())
        return uri

    def __get_admin_sentinel_connection(self, instance=None):
        sentinels = []

        if instance:
            sentinels.append((instance.address, instance.port))
        else:
            for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS_SENTINEL, is_active=True).all():
                sentinels.append((instance.address, instance.port))

        return sentinels

    def __get_admin_single_connection(self, instance=None):
        if instance:
            return instance.address, instance.port

        instances = self.databaseinfra.instances.filter(
            instance_type=Instance.REDIS, is_active=True).all()
        return instances[0].address, instances[0].port

    def __concatenate_instances_dns_only(self):
        return ",".join(["%s" % (instance.dns)
                         for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS_SENTINEL, is_active=True).all()])

    def get_dns_port(self):
        if self.databaseinfra.plan.is_ha:
            dns = self.__concatenate_instances_dns_only()
            port = self.databaseinfra.instances.filter(
                instance_type=Instance.REDIS_SENTINEL, is_active=True).all()[0].port
        else:
            instance = self.databaseinfra.instances.all()[0]
            dns = instance.dns
            port = instance.port
        return dns, port

    def get_sentinel_client(self, instance=None):
        connection_timeout_in_seconds = Configuration.get_by_name_as_int(
            'redis_connect_timeout', default=REDIS_CONNECTION_DEFAULT_TIMEOUT)
        sentinels = self.__get_admin_sentinel_connection(instance)
        sentinel = Sentinel(
            sentinels, socket_timeout=connection_timeout_in_seconds)
        return sentinel

    def __redis_client__(self, instance):

        try:
            LOG.debug(
                'Connecting to redis databaseinfra %s', self.databaseinfra)
            # redis uses timeout in seconds
            connection_timeout_in_seconds = Configuration.get_by_name_as_int(
                'redis_connect_timeout', default=REDIS_CONNECTION_DEFAULT_TIMEOUT)

            if (instance and instance.instance_type == Instance.REDIS) or (not self.databaseinfra.plan.is_ha and not instance):
                connection_address, connection_port = self.__get_admin_single_connection(
                    instance)
                client = redis.Redis(host=connection_address,
                                     port=int(connection_port),
                                     password=self.databaseinfra.password,
                                     socket_connect_timeout=connection_timeout_in_seconds)

            else:
                sentinel = self.get_sentinel_client(instance)
                client = sentinel.master_for(self.databaseinfra.name,
                                             socket_timeout=connection_timeout_in_seconds,
                                             password=self.databaseinfra.password)

            LOG.debug(
                'Successfully connected to redis databaseinfra %s' % (self.databaseinfra))
            return client
        except Exception as e:
            raise e

    def get_client(self, instance):
        return self.__redis_client__(instance)

    def lock_database(self, client):
        pass

    def unlock_database(self, client):
        pass

    @contextmanager
    def redis(self, instance=None, database=None):
        client = None
        try:
            client = self.__redis_client__(instance)

            return_value = client
            yield return_value
        except Exception as e:
            raise ConnectionError(
                'Error connecting to databaseinfra %s : %s' % (self.databaseinfra, str(e)))

    def check_status(self, instance=None):
        with self.redis(instance=instance) as client:
            try:
                ok = client.ping()
                return True
            except Exception as e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))

            if not ok:
                raise ConnectionError(
                    'Invalid status for ping command to databaseinfra %s' % self.databaseinfra)

    def list_databases(self, instance=None):
        dbs_names = []
        with self.redis(instance=instance) as client:
            try:
                keyspace = client.info('keyspace')
                if len(keyspace) == 0:
                    dbs_names.append('db0')
                else:
                    for db in keyspace:
                        dbs_names.append(db)
            except Exception as e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))
        return dbs_names

    def info(self):
        databaseinfra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra)

        with self.redis() as client:
            json_server_info = client.info()

            databaseinfra_status.version = json_server_info.get(
                'redis_version', None)
            databaseinfra_status.used_size_in_bytes = json_server_info.get(
                'used_memory', 0)

            list_databases = self.list_databases()
            for database in self.databaseinfra.databases.all():
                database_name = database.name
                db_status = DatabaseStatus(database)
                try:
                    if self.check_status():
                        db_status.is_alive = True
                except:
                    pass

                db_status.total_size_in_bytes = 0
                db_status.used_size_in_bytes = databaseinfra_status.used_size_in_bytes

                databaseinfra_status.databases_status[
                    database_name] = db_status

        return databaseinfra_status

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance):
            return 0

        with self.redis(instance=instance) as client:
            server_info = client.info()

            return int(server_info['master_last_io_seconds_ago'])

    def is_replication_ok(self, instance):
        replication_info = int(self.get_replication_info(instance=instance))

        if replication_info == 0:
            return True

        return False

    def create_user(self, credential, roles=["readWrite", "dbAdmin"]):
        pass

    def update_user(self, credential):
        pass

    def remove_user(self, credential):
        pass

    def create_database(self, database):
        pass

    def remove_database(self, database):
        pass

    def change_default_pwd(self, instance):
        pass

    def clone(self):
        return CLONE_DATABASE_SCRIPT_NAME

    def check_instance_is_eligible_for_backup(self, instance):
        if instance.instance_type == Instance.REDIS_SENTINEL:
            return False

        if self.databaseinfra.instances.count() == 1:
            return True

        with self.redis(instance=instance) as client:
            try:
                info = client.info()
                if info['role'] == 'slave':
                    return True
                else:
                    return False
            except Exception as e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))

    def check_instance_is_master(self, instance):
        if instance.instance_type == Instance.REDIS_SENTINEL:
            return False

        if self.databaseinfra.instances.count() == 1:
            return True

        with self.redis(instance=instance) as client:
            try:
                info = client.info()
                if info['role'] == 'slave':
                    return False
                else:
                    return True
            except Exception as e:
                raise ConnectionError(
                    'Error connection to databaseinfra %s: %s' % (self.databaseinfra, str(e)))

    def initialization_script_path(self,):
        return "/etc/init.d/redis"

    def deprecated_files(self,):
        return ["*.pid", ]

    def data_dir(self, ):
        return '/data/'

    def switch_master(self):

        sentinel_instance = self.databaseinfra.instances.filter(
            instance_type=Instance.REDIS_SENTINEL, is_active=True).all()[0]
        host = sentinel_instance.hostname

        host_attr = HostAttr.objects.get(host=host)

        script = """
        #!/bin/bash

        die_if_error()
        {
            local err=$?
            if [ "$err" != "0" ];
            then
                echo "$*"
                exit $err
            fi
        }"""

        script += """
        /usr/local/redis/src/redis-cli -h {} -p {} <<EOF_DBAAS
        SENTINEL failover {}
        exit
        \nEOF_DBAAS
        die_if_error "Error reseting sentinel"
        """.format(sentinel_instance.address, sentinel_instance.port, self.databaseinfra.name)

        script = build_context_script({}, script)
        output = {}
        return_code = exec_remote_command(server=host.address,
                                          username=host_attr.vm_user,
                                          password=host_attr.vm_password,
                                          command=script,
                                          output=output)
        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))

    def get_database_agents(self):
        return ['td-agent', 'httpd', 'monit']
