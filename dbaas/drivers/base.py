# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from collections import Iterable
from django.utils.translation import ugettext_lazy as _
from .errors import ConnectionError


LOG = logging.getLogger(__name__)

__all__ = ['BaseDriver', 'DatabaseStatus', 'DatabaseInfraStatus']


class BaseDriver(object):

    """
    BaseDriver interface
    """
    ENV_CONNECTION = 'DATABASEINFRA_CONNECTION'

    # List of reserved database names for this driver that cannot be used
    RESERVED_DATABASES_NAME = []

    # must be overwritten by subclasses
    default_port = 0

    def __init__(self, *args, **kwargs):

        if 'databaseinfra' in kwargs:
            self.databaseinfra = kwargs.get('databaseinfra')
            self.name = self.databaseinfra.engine.name
        else:
            raise TypeError(_("DatabaseInfra is not defined"))

    def _masters_size_in_bytes(self, field_lookup):
        masters = self.get_master_instance()
        masters = [masters] if not isinstance(masters, Iterable) else masters
        return sum(map(
            lambda m: getattr(m, field_lookup) or 0, masters
        ))

    @property
    def replication_topology(self):
        return self.databaseinfra.plan.replication_topology

    @property
    def replication_topology_driver(self):
        import util
        return util.get_replication_topology_instance(
            self.replication_topology.class_path
        )

    @property
    def masters_total_size_in_bytes(self):
        """
            Return total size of all masters instances on infra.
        """
        return self._masters_size_in_bytes('total_size_in_bytes')

    @property
    def masters_used_size_in_bytes(self):
        """
            Return used size of all masters instances on infra.
        """
        return self._masters_size_in_bytes('used_size_in_bytes')

    def test_connection(self, credential=None):
        """ Tests the connection to the database """
        raise NotImplementedError()

    def get_connection(self, database=None):
        """ Connection string for this databaseinfra """
        raise NotImplementedError()

    def get_connection_dns(self, database=None):
        """ Connection string for this databaseinfra """
        raise NotImplementedError()

    def get_user(self):
        return self.databaseinfra.user

    def get_password(self):
        return self.databaseinfra.password

    def check_status(self):
        """ Check if databaseinfra is working. If not working, raises subclass of GenericDriverError """
        raise NotImplementedError()

    def info(self):
        """ Returns a mapping with same attributes of databaseinfra """
        raise NotImplementedError()

    def get_total_size_from_instance(self, instance):
        """
            Method used in update_infra_instances_sizes.
            Return total size in bytes from instance.
        """
        raise NotImplementedError()

    def get_used_size_from_instance(self, instance):
        """
            Method used in update_infra_instances_sizes.
            Return used size in bytes from instance.
        """
        raise NotImplementedError()

    def update_infra_instances_sizes(self):
        updated_instances = []

        for instance in self.get_database_instances():
            if instance.is_alive:
                instance.used_size_in_bytes = self.get_used_size_from_instance(instance)
                instance.total_size_in_bytes = self.get_total_size_from_instance(instance)
                instance.save()
                updated_instances.append("{} - OK\n".format(instance.dns))
            else:
                updated_instances.append("{} - ERROR\n".format(instance.dns))

        return updated_instances

    def get_master_instance_total_size_in_gb(self, instance=None):
        """ Return total size of a instance.
            If instance not passed the total of first master instance
            will be returned.
        """
        from logical.models import GB_FACTOR
        if instance is None:
            instance = self.get_master_instance()
            if instance and isinstance(instance, Iterable):
                instance = instance[0]

        if hasattr(instance, 'total_size_in_bytes'):
            return (instance.total_size_in_bytes or 0) * GB_FACTOR
        return 0

    def create_user(self, credential, roles=None):
        raise NotImplementedError()

    def update_user(self, credential):
        raise NotImplementedError()

    def remove_user(self, credential):
        raise NotImplementedError()

    def list_users(self, instance=None):
        """
        this method should return a list of the users in the instance
        Ex.: ["mary", "john", "michael"]
        """
        raise NotImplementedError()

    def create_database(self, database):
        raise NotImplementedError()

    def remove_database(self, database):
        raise NotImplementedError()

    def list_databases(self):
        """
        list databases in a databaseinfra
        this method should return a list of the databases names in the instance
        Ex.: ["mary", "john", "michael"]
        """
        raise NotImplementedError()

    def import_databases(self, databaseinfra):
        """import databases already created in a databaseinfra"""
        raise NotImplementedError()

    def get_client(self, instance):
        raise NotImplementedError()

    def lock_database(self, client):
        raise NotImplementedError()

    def unlock_database(self, client):
        raise NotImplementedError()

    def check_instance_is_eligible_for_backup(self, instance):
        raise NotImplementedError()

    def check_instance_is_master(self, instance):
        raise NotImplementedError()

    def initialization_script_path(self, host=None):
        raise NotImplementedError()

    def deprecated_files(self,):
        raise NotImplementedError()

    def remove_deprectaed_files(self,):
        return str().join(["\nrm -f " + self.data_dir() + file for file in self.deprecated_files()])

    def data_dir(self, ):
        raise NotImplementedError()

    def get_replication_info(self, instance):
        raise NotImplementedError()

    def is_replication_ok(self, instance):
        raise NotImplementedError()

    def switch_master(self, instance=None):
        raise NotImplementedError()

    def get_database_instances(self, ):
        driver_name = self.name.upper()
        instances = [instance if instance.instance_type == instance.__getattribute__(
            driver_name) else None for instance in self.databaseinfra.instances.all()]
        return filter(None, instances)

    def get_non_database_instances(self, ):
        driver_name = self.name.upper()
        instances = [instance if instance.instance_type != instance.__getattribute__(
            driver_name) else None for instance in self.databaseinfra.instances.all()]
        return filter(None, instances)

    def get_master_instance(self, ):
        instances = self.get_database_instances()

        for instance in instances:
            try:
                if self.check_instance_is_master(instance):
                    return instance
            except ConnectionError:
                continue

        return None

    def get_slave_instances(self, ):
        instances = self.get_database_instances()
        master = self.get_master_instance()

        try:
            instances.remove(master)
        except ValueError:
            raise Exception("Master could not be detected")

        return instances

    def start_slave(self, instance):
        pass

    def stop_slave(self, instance):
        pass

    def agents_command(self, host, command):
        from dbaas_cloudstack.models import HostAttr
        from util import exec_remote_command

        host_attr = HostAttr.objects.get(host=host)
        for agent in self.get_database_agents():
            script = '/etc/init.d/{} {}'.format(agent, command)
            output = {}
            return_code = exec_remote_command(
                server=host.address,
                username=host_attr.vm_user,
                password=host_attr.vm_password,
                command=script,
                output=output
            )
            LOG.info(
                'Running {} - Return Code: {}. Output script: {}'.format(
                    script, return_code, output
                )
            )

    def start_agents(self, host):
        self.agents_command(host, "start")

    def stop_agents(self, host):
        self.agents_command(host, "stop")

    def check_replication_and_switch(self, instance, attempts=100, check_is_master_attempts=5):
        from time import sleep
        for attempt in range(0, attempts):
            if self.is_replication_ok(instance):
                self.switch_master(instance)
                LOG.info("Switch master returned ok...")

                check_is_master_attempts_count = check_is_master_attempts
                while self.check_instance_is_master(instance):
                    if check_is_master_attempts_count == 0:
                        break
                    check_is_master_attempts_count -= 1
                    sleep(10)
                else:
                    return

                raise Exception("Could not change master")

            LOG.info("Waiting 10s to check replication...")
            sleep(10)
        raise Exception("Could not switch master because of replication's delay")

    def get_database_agents(self):
        """ Returns database agents list"""
        raise NotImplementedError()

    def get_default_database_port(self):
        """ Returns database default port"""
        raise NotImplementedError()

    def get_default_instance_type(self):
        """ Returns default instance type"""
        raise NotImplementedError()

    @property
    def database_key(self):
        return None

    @property
    def replica_set_name(self):
        return None

    def get_configuration(self):
        raise NotImplementedError

    def set_configuration(self, instance, name, value):
        raise NotImplementedError

    def get_database_process_name(self):
        """ Returns OS database process name"""
        raise NotImplementedError

    def initialization_parameters(self, instance):
        return {}

    def configuration_parameters(self, instance):
        return {}

    def configuration_parameters_for_log_resize(self, instance):
        return {}

    def configuration_parameters_migration(self, instance):
        return self.configuration_parameters(instance)

    @classmethod
    def topology_name(cls):
        return []


class DatabaseStatus(object):

    def __init__(self, database_model):
        self.database_model = database_model
        self.used_size_in_bytes = -1
        self.total_size_in_bytes = -1
        self.is_alive = False

    @property
    def name(self):
        return self.database_model.name


class DatabaseInfraStatus(object):

    def __init__(self, databaseinfra_model):
        self.databaseinfra_model = databaseinfra_model
        self.version = None
        self.used_size_in_bytes = -1
        self.databases_status = {}

    def get_database_status(self, database_name):
        """ Return DatabaseStatus of one specific database """
        return self.databases_status.get(database_name, None)
