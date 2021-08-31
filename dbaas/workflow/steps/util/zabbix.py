# -*- coding: utf-8 -*-
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseInstanceStep
import copy


class ZabbixStep(BaseInstanceStep):

    def __init__(self, instance):
        super(ZabbixStep, self).__init__(instance)
        self.provider = None

    @property
    def credentials(self):
        integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
        return Credential.get_credentials(self.environment, integration)

    @property
    def can_run(self):
        try:
            _ = self.credentials
        except IndexError:
            return False
        else:
            return True

    @property
    def instances(self):
        host = self.host
        if self.host_migrate:
            host = self.instance.hostname
        return host.instances.all()

    @property
    def zabbix_provider(self):
        if not self.provider:
            infra = self.infra
            if self.plan != self.target_plan:
                infra = copy.deepcopy(self.infra)
                target_plan = self.target_plan
                infra.plan = target_plan
                infra.engine = target_plan.engine
                infra.engine_patch = target_plan.engine.default_engine_patch
            self.provider = factory_for(
                databaseinfra=infra,
                credentials=self.credentials
            )
        return self.provider

    @property
    def hosts_in_zabbix(self):
        monitors = [self.host.hostname]
        for instance in self.instances:
            current_dns = instance.dns
            monitors.append(current_dns)

            zabbix_extras = self.zabbix_provider.get_zabbix_databases_hosts()
            for zabbix_extra in zabbix_extras:
                if current_dns in zabbix_extra and zabbix_extra != current_dns:
                    monitors.append(zabbix_extra)

        return monitors

    @property
    def target_plan(self):
        return self.plan

    def __del__(self):
        if self.provider:
            self.zabbix_provider.logout()

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class DestroyAlarms(ZabbixStep):

    def __unicode__(self):
        return "Destroying Zabbix alarms..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        if not self.host:
            return
        for host in self.hosts_in_zabbix:
            if self.zabbix_provider.get_host_triggers(host):
                self.zabbix_provider.delete_instance_monitors(host)


class CreateAlarms(ZabbixStep):

    def __unicode__(self):
        return "Creating Zabbix alarms..."

    @property
    def engine_version(self):
        return self.instance.databaseinfra.engine.version

    def do(self):
        if not self.is_valid:
            return

        DestroyAlarms(self.instance).do()
        self.zabbix_provider.create_instance_basic_monitors(
            self.host
        )

        for instance in self.instances:
            self.zabbix_provider.create_instance_monitors(instance)

    def undo(self):
        DestroyAlarms(self.instance).do()


class CreateAlarmsDatabaseMigrateBase(ZabbixStep):

    @property
    def environment(self):
        raise NotImplementedError

    @property
    def host_monitor(self):
        return NotImplementedError

    @property
    def instances_monitor(self):
        return self.host_monitor.instances.all()

    @property
    def hosts_in_zabbix(self):
        monitors = [self.host_monitor.hostname]
        for instance in self.instances_monitor:
            current_dns = instance.dns
            monitors.append(current_dns)

            zabbix_extras = self.zabbix_provider.get_zabbix_databases_hosts()
            for zabbix_extra in zabbix_extras:
                if current_dns in zabbix_extra and zabbix_extra != current_dns:
                    monitors.append(zabbix_extra)

        return monitors

    def _create_alarms(self):
        self.zabbix_provider.create_instance_basic_monitors(self.host_monitor)
        for instance in self.instances_monitor:
            self.zabbix_provider.create_instance_monitors(instance)

    def _destroy_alarms(self):
        for host in self.hosts_in_zabbix:
            if self.zabbix_provider.get_host_triggers(host):
                self.zabbix_provider.delete_instance_monitors(host)

    def do(self):
        self._destroy_alarms()
        self._create_alarms()

    def undo(self):
        self._destroy_alarms()


class CreateAlarmsDatabaseMigrate(CreateAlarmsDatabaseMigrateBase):

    def __unicode__(self):
        return "Recreating Zabbix alarms..."

    @property
    def environment(self):
        return self.host_migrate.environment

    @property
    def host_monitor(self):
        return self.instance.hostname.future_host

class DestroyAlarmsDatabaseMigrate(CreateAlarmsDatabaseMigrateBase):

    def __unicode__(self):
        return "Destroying Zabbix alarms..."

    @property
    def environment(self):
        return self.infra.environment

    @property
    def host_monitor(self):
        return self.instance.hostname

    def do(self):
        self._destroy_alarms()

    def undo(self):
        self._destroy_alarms()
        self._create_alarms()


class CreateAlarmsForUpgrade(CreateAlarms):

    @property
    def target_plan(self):
        return self.plan.engine_equivalent_plan


class CreateAlarmsForMigrateEngine(CreateAlarms):

    @property
    def target_plan(self):
        return self.plan.migrate_engine_equivalent_plan


class DisableAlarms(ZabbixStep):

    def __unicode__(self):
        return "Disabling Zabbix alarms..."

    def do(self):
        self.zabbix_provider.disable_alarms()

    def undo(self):
        self.zabbix_provider.enable_alarms()


class EnableAlarms(ZabbixStep):

    def __unicode__(self):
        return "Enabling Zabbix alarms..."

    def do(self):
        self.zabbix_provider.enable_alarms()

    def undo(self):
        self.zabbix_provider.disable_alarms()


class UpdateMonitoring(ZabbixStep):
    def __init__(self, instance, hostgroup_name=None):
        super(UpdateMonitoring, self).__init__(instance)
        self.hostgroup_name = hostgroup_name

    @property
    def is_valid(self):
        if self.hostgroup_name:
            return True
        return False


class UpdateMonitoringAddHostgroup(UpdateMonitoring):
    def __unicode__(self):
        return "Adding HostGroup on Monitoring..."

    def do(self):
        if not self.is_valid:
            return

        for host_name in self.hosts_in_zabbix:
            self.zabbix_provider.add_hostgroup_on_host(
                 host_name=host_name,
                 hostgroup_name=self.hostgroup_name)


class UpdateMonitoringRemoveHostgroup(UpdateMonitoring):
    def __unicode__(self):
        return "Removing HostGroup on Monitoring..."

    def do(self):
        if not self.is_valid:
            return

        for host_name in self.hosts_in_zabbix:
            self.zabbix_provider.remove_hostgroup_on_host(
                 host_name=host_name,
                 hostgroup_name=self.hostgroup_name)

class UpdateMongoDBSSL(ZabbixStep):

    def __unicode__(self):
        return "Update SSL info on Zabbix..."

    @property
    def is_valid(self):
        return self.instance.is_database

    def do(self):
        if not self.is_valid:
            return

        if self.infra.ssl_mode == self.infra.REQUIRETLS:
            value = 'True'
        else:
            value = 'False'

        self.zabbix_provider.update_macro(
            host_name=self.instance.dns,
            macro='{$MONGO_SSL}',
            value=value
        )