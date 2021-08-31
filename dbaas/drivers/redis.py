# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from time import sleep
import logging
import redis
from redis.sentinel import Sentinel
from rediscluster import StrictRedisCluster
from contextlib import contextmanager

from drivers import BaseDriver, DatabaseInfraStatus, DatabaseStatus
from drivers.errors import ConnectionError
from system.models import Configuration
from physical.models import Instance
from util import build_context_script, \
    make_db_random_password



LOG = logging.getLogger(__name__)

CLONE_DATABASE_SCRIPT_NAME = "redis_clone.py"
REDIS_CONNECTION_DEFAULT_TIMEOUT = 5
REDIS_CONNECTION_SOCKET_TIMEOUT = 3


class Redis(BaseDriver):

    default_port = 6379

    @property
    def ports(self):
        return (6379,)

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

    @property
    def connection_socket_timeout_in_seconds(self):
        return Configuration.get_by_name_as_int(
            'redis_socket_connect_timeout',
            default=REDIS_CONNECTION_SOCKET_TIMEOUT
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

    def __redis_client__(self, instance, default_timeout=False):
        LOG.debug('Connecting to redis single infra {}'.format(
            self.databaseinfra
        ))

        address, port = self.__get_admin_single_connection(instance)
        client = redis.StrictRedis(
            host=address, port=int(port),
            password=self.databaseinfra.password,
            socket_timeout=REDIS_CONNECTION_DEFAULT_TIMEOUT if default_timeout else self.connection_timeout_in_seconds,
            socket_connect_timeout= REDIS_CONNECTION_SOCKET_TIMEOUT if default_timeout else self.connection_socket_timeout_in_seconds
        )

        LOG.debug('Successfully connected to redis single infra {}'.format(
            self.databaseinfra
        ))

        return client

    def get_client(self, instance):
        return self.__redis_client__(instance, default_timeout=False)

    def lock_database(self, client):
        pass

    def unlock_database(self, client):
        pass

    @contextmanager
    def redis(self, instance=None, database=None, default_timeout=False):
        try:
            client = self.__redis_client__(instance, default_timeout=default_timeout)
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

    def check_instance_is_master(self, instance, default_timeout=False):
        if instance.is_active:
            return True
        return False

    def deprecated_files(self,):
        return ["*.pid", ]

    def data_dir(self, ):
        return '/data/'

    def switch_master(self, instance=None, preferred_slave_instance=None):
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
            config = client.config_get()

            if 'client-output-buffer-limit' in config:
                config_COBL = config['client-output-buffer-limit']
                config_COBL_normal = config_COBL.split("normal ")[1].split(" slave")[0]
                config_COBL_slave = config_COBL.split("slave ")[1].split(" pubsub")[0]
                config_COBL_pubsub = config_COBL.split("pubsub ")[1]
                config['client-output-buffer-limit-normal'] = config_COBL_normal
                config['client-output-buffer-limit-slave'] = config_COBL_slave
                config['client-output-buffer-limit-pubsub'] = config_COBL_pubsub

            return config

    def set_configuration(self, instance, name, value):
        with self.redis(instance) as client:
            if name.startswith('client-output-buffer-limit-'):
                name, prefix = name.rsplit("-", 1)
                value = '{} {}'.format(prefix, value)

            client.config_set(name, value)

    def get_database_process_name(self):
        return "redis-server"

    def initialization_parameters(self, instance):
        return self.parameters_redis(instance.hostname)

    def configuration_parameters(self, instance, **kw):
        config = self.parameters_redis(instance.hostname)
        config.update(kw)
        return config

    def parameters_redis(self, host):
        redis = host.database_instance()
        redis_address = redis.address
        if host.future_host:
            redis_address = host.future_host.address
        redis_port = redis.port
        only_sentinel = False

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
            'ONLY_SENTINEL': only_sentinel,
            'DATABASE_START_COMMAND': host.commands.database(
                action='start'
            ),
            'HTTPD_STOP_COMMAND_NO_OUTPUT': host.commands.httpd(
                action='stop',
                no_output=True
            ),
            'HTTPD_START_COMMAND_NO_OUTPUT': host.commands.httpd(
                action='start',
                no_output=True
            ),
            'SECONDARY_SERVICE_START_COMMAND': host.commands.secondary_service(
                action='start'
            )
        }

    def configuration_parameters_migration(self, instance):
        return self.configuration_parameters(instance)

    @classmethod
    def topology_name(cls):
        return ['redis_single']

    def build_new_infra_auth(self):
        return '', make_db_random_password(), ''

    def create_metric_collector_user(self, username, password):
        pass

    def remove_metric_collector_user(self, username):
        pass

    def get_metric_collector_user(self, username):
        return ""

    def get_metric_collector_password(self, password):
        return self.databaseinfra.password

class RedisSentinel(Redis):

    @property
    def ports(self):
        return (6379, 26379)

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

    def __redis_client__(self, instance, default_timeout=False):
        if instance and instance.instance_type == Instance.REDIS:
            return super(RedisSentinel, self).__redis_client__(instance, default_timeout=False)

        LOG.debug('Connecting to redis infra {}'.format(self.databaseinfra))

        sentinel = self.get_sentinel_client(instance)
        client = sentinel.master_for(
            self.databaseinfra.name,
            socket_timeout=REDIS_CONNECTION_DEFAULT_TIMEOUT if default_timeout else self.connection_timeout_in_seconds,
            socket_connect_timeout=REDIS_CONNECTION_SOCKET_TIMEOUT if default_timeout else self.connection_socket_timeout_in_seconds,
            password=self.databaseinfra.password
        )

        LOG.debug('Successfully connected to redis infra {}'.format(
            self.databaseinfra
        ))
        return client

    def get_sentinel_client(self, instance=None):
        sentinels = self.__get_admin_sentinel_connection(instance)
        sentinel = Sentinel(
            sentinels, socket_timeout=self.connection_timeout_in_seconds, socket_connect_timeout=self.connection_socket_timeout_in_seconds
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

    def get_sentinel_instance_client(self, instance, default_timeout=False):
        if instance.instance_type != Instance.REDIS_SENTINEL:
            error = 'Instance {} is not Sentinel'.format(instance)
            raise Exception(error)
        address, port = instance.address, instance.port
        client = redis.StrictRedis(
            host=address, port=int(port),
            socket_timeout=REDIS_CONNECTION_DEFAULT_TIMEOUT if default_timeout else self.connection_timeout_in_seconds,
            socket_connect_timeout= REDIS_CONNECTION_SOCKET_TIMEOUT if default_timeout else self.connection_socket_timeout_in_seconds
        )
        return client

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance, default_timeout=False):
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

    def check_instance_is_master(self, instance, default_timeout=False):
        if instance.instance_type == Instance.REDIS_SENTINEL:
            return False
        
        if not instance.is_active:
            return False

        masters_for_sentinel = []
        sentinels = self.get_non_database_instances()

        for sentinel in sentinels:
            client = self.get_sentinel_instance_client(sentinel)
            try:
                master = client.sentinel_get_master_addr_by_name(
                    self.databaseinfra.name)
                masters_for_sentinel.append(master)
            except Exception as e:
                error = 'Connection error to {}. Error: {}'.format(
                    sentinel, e)
                LOG.info(error)

        sentinels_believe_is_master = 0
        for master_host, master_port in masters_for_sentinel:
            if (instance.address == master_host and
                instance.port == master_port):
                sentinels_believe_is_master += 1

        if sentinels_believe_is_master > 1:
            return True

        return False

    def switch_master(self, instance=None, preferred_slave_instance=None):
        sentinel_instance = self.instances_filtered.first()
        host = sentinel_instance.hostname

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
        host.ssh.run_script(script)

    def configuration_parameters(self, instance, **kw):
        variables = {}
        if kw.get('need_master', False):
            for i in range(5):
                master = self.get_master_instance()
                if master:
                    break
                sleep(10)
            if not master:
                raise Exception(
                    ("Expect got master instance but got {} on "
                     "configuration_parameters").format(
                        master
                    )
                )
        master = self.get_master_instance()
        if master:
            variables.update(self.master_parameters(instance, master))

        variables.update(self.parameters_redis(instance.hostname))
        variables.update(self.parameters_sentinel(instance.hostname))
        variables.update(kw)

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

        if redis and host.future_host:
            redis_address = host.future_host.address

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
            'ONLY_SENTINEL': only_sentinel,
            'DATABASE_START_COMMAND': host.commands.database(
                action='start'
            ),
            'HTTPD_STOP_COMMAND_NO_OUTPUT': host.commands.httpd(
                action='stop',
                no_output=True
            ),
            'HTTPD_START_COMMAND_NO_OUTPUT': host.commands.httpd(
                action='start',
                no_output=True
            ),
            'SECONDARY_SERVICE_START_COMMAND': host.commands.secondary_service(
                action='start'
            )
        }

    def master_parameters(self, instance, master):

        return {
            'SENTINELMASTER': master.address,
            'SENTINELMASTERPORT': master.port,
            'MASTERNAME': instance.databaseinfra.name
        }

    def parameters_sentinel(self, host):
        sentinel = host.non_database_instance()
        if sentinel and host.future_host:
            sentinel.address = host.future_host.address

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
    def ports(self):
        return (6379, 16379)

    @property
    def uri_instance_type(self):
        return 'cluster'

    def get_dns_port(self):
        dns = self.concatenate_instances_dns_only()
        port = self.instances_filtered.first().port
        return dns, port

    def __redis_client__(self, instance, default_timeout=False):
        LOG.debug('Connecting to redis infra {}'.format(self.databaseinfra))

        cluster = self.get_cluster_client(instance, default_timeout=default_timeout)

        LOG.debug('Successfully connected to redis infra {}'.format(
            self.databaseinfra
        ))

        return cluster

    def get_cluster_client(self, instance, default_timeout=False):
        if instance:
            return redis.StrictRedis(
                host=instance.address, port=instance.port,
                password=self.databaseinfra.password,
                socket_timeout=REDIS_CONNECTION_DEFAULT_TIMEOUT if default_timeout else self.connection_timeout_in_seconds,
                socket_connect_timeout=REDIS_CONNECTION_SOCKET_TIMEOUT if default_timeout else self.connection_socket_timeout_in_seconds,
            )

        return StrictRedisCluster(
            startup_nodes=[
                {'host': instance.address, 'port': instance.port}
                for instance in self.instances_filtered
            ],
            password=self.databaseinfra.password,
            socket_timeout=REDIS_CONNECTION_DEFAULT_TIMEOUT if default_timeout else self.connection_timeout_in_seconds,
            socket_connect_timeout=REDIS_CONNECTION_SOCKET_TIMEOUT if default_timeout else self.connection_socket_timeout_in_seconds,
        )

    def get_replication_info(self, instance):
        if self.check_instance_is_master(instance=instance, default_timeout=False):
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

    def check_instance_is_master(self, instance, default_timeout=False):
        if not instance.is_active:
            return False

        with self.redis(instance=instance, default_timeout=default_timeout) as client:
            try:
                info = client.info()
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))
            else:
                return info['role'] == 'master'

    def switch_master(self, instance=None, preferred_slave_instance=None):
        if instance is None:
            raise Exception('Cannot switch master in a redis cluster without instance.')

        slave_instance = self.get_slave_for(instance, preferred_slave_instance)
        if not slave_instance:
            raise Exception('There is no slave for {}'.format(instance))
        host = slave_instance.hostname

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

        host.ssh.run_script(script)

    def get_master_instance(self):
        masters = []
        for instance in self.get_database_instances():
            try:
                if self.check_instance_is_master(instance, default_timeout=False):
                    masters.append(instance)
                if instance.hostname.future_host:
                    instance.address = instance.hostname.future_host.address
                    if self.check_instance_is_master(instance, default_timeout=False):
                        masters.append(instance)
            except ConnectionError:
                continue

        return masters

    def get_master_instance2(self):
        masters = []
        for instance in self.get_database_instances():
            try:
                if self.check_instance_is_master(instance, default_timeout=False):
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
                return instance

            address = info['master_host']
            port = info['master_port']

            return self.databaseinfra.instances.filter(
                hostname__address=address, port=port
            ).first()

    def get_slave_for(self, instance, preferred_slave_instance=None):
        with self.redis(instance=instance) as client:
            try:
                info = client.info('replication')
            except Exception as e:
                raise ConnectionError('Error connection to infra {}: {}'.format(
                    self.databaseinfra, str(e)
                ))

            if info['role'] != 'master':
                return

            connected_slaves = info['connected_slaves']
            if connected_slaves == 0:
                return
            
            if preferred_slave_instance is None:
                address = info['slave0']['ip']
                port = info['slave0']['port']

            for i in range(connected_slaves):
                address = info['slave{}'.format(i)]['ip']
                port = info['slave{}'.format(i)]['port']
                if (address == preferred_slave_instance.address
                    and port == preferred_slave_instance.port):
                    break
                   
            return self.databaseinfra.instances.filter(
                hostname__address=address, port=port
            ).first()

    @classmethod
    def topology_name(cls):
        return ['redis_cluster']

    def get_node_id(self, instance, address, port):
        name = "{}:{}".format(address, port)
        with self.redis(instance=instance) as client:
            nodes = client.execute_command("CLUSTER NODES")

        for node in nodes.keys():
            if name in node:
                return nodes[node]['node_id']
        raise EnvironmentError('Node {} not in {}'.format(name, nodes))
