# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import redis
from redis.sentinel import Sentinel
from rediscluster import StrictRedisCluster
from contextlib import contextmanager

from drivers import BaseDriver, DatabaseInfraStatus, DatabaseStatus
from drivers.errors import ConnectionError
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

    @property
    def instances_filtered(self):
        return self.databaseinfra.instances.filter(
            instance_type=Instance.REDIS, is_active=True
        )

    @property
    def uri_instance_type(self):
        return 'redis'

    @property
    def database_name(self):
        return '0'

    @property
    def connection_timeout_in_seconds(self):
        return Configuration.get_by_name_as_int(
            'redis_connect_timeout',
            default=REDIS_CONNECTION_DEFAULT_TIMEOUT
        )

    def concatenate_instances(self):
        return ",".join([
            "{}:{}".format(instance.address, instance.port)
            for instance in self.instances_filtered
        ])

    def concatenate_instances_dns(self):
        return ",".join([
            "{}:{}".format(instance.dns, instance.port)
            for instance in self.instances_filtered
            if not instance.dns.startswith('10.')
        ])

    def concatenate_instances_dns_only(self):
        return ",".join([
            str(instance.dns) for instance in self.instances_filtered
        ])

    def get_connection(self, database=None):
        return "{}://:<password>@{}/{}".format(
            self.uri_instance_type, self.concatenate_instances(),
            self.database_name
        )

    def get_connection_dns(self, database=None):
        return "{}://:<password>@{}/{}".format(
            self.uri_instance_type, self.concatenate_instances_dns(),
            self.database_name
        )

    def get_connection_dns_simple(self, database=None):
        return "{}://{}".format(
            self.uri_instance_type, self.concatenate_instances_dns()
        )

    def __get_admin_single_connection(self, instance=None):
        if not instance:
            instance = self.instances_filtered.first()

        return instance.address, instance.port

    def get_dns_port(self):
        instance = self.databaseinfra.instances.first()
        return instance.dns, instance.port

    def __redis_client__(self, instance):
        LOG.debug('Connecting to redis single infra {}'.format(
            self.databaseinfra
        ))

        address, port = self.__get_admin_single_connection(instance)
        client = redis.StrictRedis(
            host=address, port=int(port),
            password=self.databaseinfra.password,
            socket_timeout=self.connection_timeout_in_seconds
        )

        LOG.debug('Successfully connected to redis single infra {}'.format(
            self.databaseinfra
        ))

        return client

    def get_client(self, instance):
        return self.__redis_client__(instance)

    def lock_database(self, client):
        pass

    def unlock_database(self, client):
        pass

    @contextmanager
    def redis(self, instance=None, database=None):
        try:
            client = self.__redis_client__(instance)
            return_value = client
            yield return_value
        except Exception as e:
            raise ConnectionError(
                'Error connecting to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                )
            )

    def check_status(self, instance=None):
        with self.redis(instance=instance) as client:
            try:
                ok = client.ping()
            except Exception as e:
                raise ConnectionError(
                    'Error connection to infra {}: {}'.format(
                        self.databaseinfra, str(e)
                    )
                )

            if not ok:
                raise ConnectionError(
                    'Invalid status for ping command to infra {}'.format(
                        self.databaseinfra
                    )
                )

        return True

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
                    'Error connection to infra {}: {}'.format(
                        self.databaseinfra, str(e)
                    )
                )

        return dbs_names

    @property
    def maxmemory(self):
        return int(
            self.databaseinfra.get_parameter_value_by_parameter_name('maxmemory') or
            self.databaseinfra.get_dbaas_parameter_default_value('maxmemory')
        )

    def get_total_size_from_instance(self, instance):
        return self.maxmemory

    def get_used_size_from_instance(self, instance):
        with self.redis(instance=instance) as client:
            if instance.status == Instance.ALIVE:
                database_info = client.info()
                return database_info.get(
                    'used_memory', 0
                )

    def info(self):
        infra_status = DatabaseInfraStatus(
            databaseinfra_model=self.databaseinfra
        )

        with self.redis() as client:
            json_server_info = client.info()

            infra_status.version = json_server_info.get(
                'redis_version', None
            )
            infra_status.used_size_in_bytes = json_server_info.get(
                'used_memory', 0
            )

            for database in self.databaseinfra.databases.all():
                database_name = database.name
                db_status = DatabaseStatus(database)

                try:
                    if self.check_status():
                        db_status.is_alive = True
                except:
                    pass

                db_status.total_size_in_bytes = 0
                db_status.used_size_in_bytes = infra_status.used_size_in_bytes

                infra_status.databases_status[database_name] = db_status

        return infra_status

    def get_replication_info(self, instance):
        return 0

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
        return True

    def check_instance_is_master(self, instance):
        return True

    def initialization_script_path(self, host=None):
        if not host:
            return '/etc/init.d/redis {option}'

        script = ''
        for instance in host.instances.all():
            if instance.is_redis:
                script += "/etc/init.d/redis {option}; "

            if instance.is_sentinel:
                script += "/etc/init.d/sentinel {option}; "

        return script

    def deprecated_files(self,):
        return ["*.pid", ]

    def data_dir(self, ):
        return '/data/'

    def switch_master(self, instance=None):
        pass

    def get_database_agents(self):
        return ['httpd']

    def get_default_database_port(self):
        return 6379

    def get_default_instance_type(self):
        return Instance.REDIS

    def get_configuration(self):
        instance = self.databaseinfra.instances.filter(
            status=Instance.ALIVE, instance_type=Instance.REDIS, is_active=True
        ).first()

        if not instance:
            raise EnvironmentError(
                'Cannot get configuration to {}. No Redis instance with status '
                'alive and active found'.format(self.databaseinfra)
            )

        with self.redis(instance) as client:
            return client.config_get()

    def set_configuration(self, instance, name, value):
        with self.redis(instance) as client:
            client.config_set(name, value)

    def get_database_process_name(self):
        return "redis-server"

    def initialization_parameters(self, instance):
        return self.parameters_redis(instance.hostname)

    def configuration_parameters(self, instance):
        return self.parameters_redis(instance.hostname)

    def parameters_redis(self, host):
        redis = host.database_instance()
        redis_address = redis.address
        redis_port = redis.port
        only_sentinel = False

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
            'ONLY_SENTINEL': only_sentinel,
        }

    def configuration_parameters_migration(self, instance):
        return self.configuration_parameters(instance)

    @classmethod
    def topology_name(cls):
        return ['redis_single']


class RedisSentinel(Redis):

    @property
    def instances_filtered(self):
        return self.databaseinfra.instances.filter(
            instance_type=Instance.REDIS_SENTINEL, is_active=True
        )

    @property
    def uri_instance_type(self):
        return 'sentinel'

    @property
    def database_name(self):
        return 'service_name:{}'.format(self.databaseinfra.name)

    def get_dns_port(self):
        dns = self.concatenate_instances_dns_only()
        port = self.instances_filtered.first().port
        return dns, port

    def __redis_client__(self, instance):
        if instance and instance.instance_type == Instance.REDIS:
            return super(RedisSentinel, self).__redis_client__(instance)

        LOG.debug('Connecting to redis infra {}'.format(self.databaseinfra))

        sentinel = self.get_sentinel_client(instance)
        client = sentinel.master_for(
            self.databaseinfra.name,
            socket_timeout=self.connection_timeout_in_seconds,
            password=self.databaseinfra.password
        )

        LOG.debug('Successfully connected to redis infra {}'.format(
            self.databaseinfra
        ))

        return client

    def get_sentinel_client(self, instance=None):
        sentinels = self.__get_admin_sentinel_connection(instance)
        sentinel = Sentinel(
            sentinels, socket_timeout=self.connection_timeout_in_seconds
        )
        return sentinel

    def __get_admin_sentinel_connection(self, instance=None):
        sentinels = []

        if instance:
            sentinels.append((instance.address, instance.port))
        else:
            for instance in self.databaseinfra.instances.filter(instance_type=Instance.REDIS_SENTINEL, is_active=True).all():
                sentinels.append((instance.address, instance.port))

        return sentinels

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance):
            return 0

        with self.redis(instance=instance) as client:
            server_info = client.info()
            return int(server_info['master_last_io_seconds_ago'])

    def check_instance_is_eligible_for_backup(self, instance):
        if instance.instance_type == Instance.REDIS_SENTINEL:
            return False

        with self.redis(instance=instance) as client:
            try:
                info = client.info()
                return info['role'] == 'slave'
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))

    def check_instance_is_master(self, instance):
        if instance.instance_type == Instance.REDIS_SENTINEL:
            return False

        with self.redis(instance=instance) as client:
            try:
                info = client.info()
                return info['role'] != 'slave'
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))

    def switch_master(self, instance=None):
        sentinel_instance = self.instances_filtered.first()
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
        """.format(
            sentinel_instance.address, sentinel_instance.port,
            self.databaseinfra.name
        )

        script = build_context_script({}, script)
        output = {}
        return_code = exec_remote_command(
            server=host.address, username=host_attr.vm_user,
            password=host_attr.vm_password, command=script, output=output
        )

        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))

    def configuration_parameters(self, instance):
        variables = {}

        master = self.get_master_instance()
        if master:
            variables.update(self.master_parameters(instance, master))

        variables.update(self.parameters_redis(instance.hostname))
        variables.update(self.parameters_sentinel(instance.hostname))

        return variables

    def parameters_redis(self, host):
        redis = host.database_instance()
        redis_address = ''
        redis_port = ''
        only_sentinel = True
        if redis:
            redis_address = redis.address
            redis_port = redis.port
            only_sentinel = False

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
            'ONLY_SENTINEL': only_sentinel,
        }

    def master_parameters(self, instance, master):
        return {
            'SENTINELMASTER': master.address,
            'SENTINELMASTERPORT': master.port,
            'MASTERNAME': instance.databaseinfra.name
        }

    def parameters_sentinel(self, host):
        sentinel = host.non_database_instance()
        sentinel_address = ''
        sentinel_port = ''
        if sentinel:
            sentinel_address = sentinel.address
            sentinel_port = sentinel.port

        return {
            'SENTINELADDRESS': sentinel_address,
            'SENTINELPORT': sentinel_port,
        }

    def configuration_parameters_migration(self, instance):
        base_parameters = super(
            RedisSentinel, self
        ).configuration_parameters_migration(instance)

        all_instances = self.databaseinfra.instances.all()
        future_master = all_instances[len(all_instances)/2]
        base_parameters.update(self.master_parameters(instance, future_master))

        return base_parameters

    @classmethod
    def topology_name(cls):
        return ['redis_sentinel']


class RedisCluster(Redis):

    @property
    def uri_instance_type(self):
        return 'cluster'

    def get_dns_port(self):
        dns = self.concatenate_instances_dns_only()
        port = self.instances_filtered.first().port
        return dns, port

    def __redis_client__(self, instance):
        LOG.debug('Connecting to redis infra {}'.format(self.databaseinfra))

        cluster = self.get_cluster_client(instance)

        LOG.debug('Successfully connected to redis infra {}'.format(
            self.databaseinfra
        ))

        return cluster

    def get_cluster_client(self, instance):
        if instance:
            return redis.StrictRedis(
                host=instance.address, port=instance.port,
                password=self.databaseinfra.password,
                socket_timeout=self.connection_timeout_in_seconds,
            )

        return StrictRedisCluster(
            startup_nodes=[
                {'host': instance.address, 'port': instance.port}
                for instance in self.instances_filtered
            ],
            password=self.databaseinfra.password,
            socket_timeout=self.connection_timeout_in_seconds,
        )

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance):
            return 0

        with self.redis(instance=instance) as client:
            info = client.info()
            return int(info['master_last_io_seconds_ago'])

    def check_instance_is_eligible_for_backup(self, instance):
        with self.redis(instance=instance) as client:
            try:
                info = client.info()
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))
            else:
                return info['role'] == 'slave'

    def check_instance_is_master(self, instance):
        with self.redis(instance=instance) as client:
            try:
                info = client.info()
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))
            else:
                return info['role'] == 'master'

    def switch_master(self, instance=None):
        if instance is None:
            raise Exception('Cannot switch master in a redis cluster without instance.')

        slave_instance = self.get_slave_for(instance)
        if not slave_instance:
            raise Exception('There is no slave for {}'.format(instance))
        host = slave_instance.hostname
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
        /usr/local/redis/src/redis-cli -h {} -p {} -a {} -c<<EOF_DBAAS
        CLUSTER FAILOVER
        exit
        \nEOF_DBAAS
        die_if_error "Error executing cluster failover"
        """.format(
            slave_instance.address, slave_instance.port,
            self.databaseinfra.password
        )

        script = build_context_script({}, script)
        output = {}
        return_code = exec_remote_command(
            server=host.address, username=host_attr.vm_user,
            password=host_attr.vm_password, command=script, output=output
        )

        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))

    def get_master_instance(self):
        masters = []
        for instance in self.get_database_instances():
            try:
                if self.check_instance_is_master(instance):
                    masters.append(instance)
            except ConnectionError:
                continue

        return masters

    def get_slave_instances(self, ):
        instances = self.get_database_instances()
        masters = self.get_master_instance()

        try:
            instances.remove(masters)
        except ValueError:
            raise Exception("Master could not be detected")

        return instances

    def get_master_for(self, instance):
        with self.redis(instance=instance) as client:
            try:
                info = client.info()
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))

            if info['role'] != 'slave':
                return

            address = info['master_host']
            port = info['master_port']

            return self.databaseinfra.instances.filter(
                hostname__address=address, port=port
            ).first()

    def get_slave_for(self, instance):
        with self.redis(instance=instance) as client:
            try:
                info = client.info()
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))

            if info['role'] != 'master':
                return

            address = info['slave0']['ip']
            port = info['slave0']['port']

            return self.databaseinfra.instances.filter(
                hostname__address=address, port=port
            ).first()

    @classmethod
    def topology_name(cls):
        return ['redis_cluster']
