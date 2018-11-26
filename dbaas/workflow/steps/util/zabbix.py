# -*- coding: utf-8 -*-
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from dbaas_zabbix import factory_for
from workflow.steps.util.base import BaseInstanceStep


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
        return self.host.instances.all()

    @property
    def zabbix_provider(self):
        if not self.provider:
            self.provider = factory_for(
                databaseinfra=self.instance.databaseinfra,
                credentials=self.credentials
            )
        return self.provider

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


class CreateAlarmsForUpgrade(CreateAlarms):

    @property
    def engine_version(self):
        return self.plan.engine_equivalent_plan.engine.version


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
