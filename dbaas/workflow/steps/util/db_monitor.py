# -*- coding: utf-8 -*-
from dbaas_dbmonitor.provider import DBMonitorProvider
from workflow.steps.util.base import BaseInstanceStep


class DBMonitorStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DBMonitorStep, self).__init__(instance)
        self.provider = DBMonitorProvider()

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class DisableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Disabling DB Monitor..."

    def do(self):
        self.provider.disabled_dbmonitor_monitoring_instance(self.instance)


class EnableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Enabling DB Monitor..."

    def do(self):
        self.provider.enabled_dbmonitor_monitoring_instance(self.instance)


class CreateMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Creating DB Monitor..."

    def do(self):
        instance_number = self.instance.databaseinfra.last_vm_created
        self.provider.create_dbmonitor_instance_monitoring(
            self.instance, instance_number
        )

    def undo(self):
        DisableMonitoring(self.instance).do()


class DisableInfraMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Disabling DB Monitor..."

    def do(self):
        self.provider.remove_dbmonitor_monitoring(self.infra)


class CreateInfraMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Creating DB Monitor..."

    def do(self):
        if self.instance == self.infra.instances.all()[0]:
            if not self.provider.get_dbmonitor_databaseinfra(self.infra):
                self.provider.create_dbmonitor_monitoring(self.infra)

    def undo(self):
        if self.instance == self.infra.instances.all()[0]:
            DisableInfraMonitoring(self.instance).do()


class UpdateInfraVersion(DBMonitorStep):
    def __unicode__(self):
        return "Update version on DB Monitor..."

    @property
    def is_valid(self):
        if self.upgrade and self.instance == self.infra.instances.all()[0]:
            return True
        return False

    def do(self):
        if self.is_valid:
            self.provider.update_dbmonitor_database_version(
                self.infra, self.upgrade.target_plan.engine.version)

    def undo(self):
        if self.is_valid:
            self.provider.update_dbmonitor_database_version(
                self.infra, self.upgrade.source_plan.engine.version)

class UpdateInfraCloudDatabaseMigrate(DBMonitorStep):
    def __unicode__(self):
        return "Update info about cloud on DBMonitor..."

    def do(self):
        self.provider.update_database_cloud(
            self.infra, self.environment.cloud.name)


class UpdateInfraOrganizationName(DBMonitorStep):
    def __unicode__(self):
        return "Update info about organization on DBMonitor..."

    def __init__(self, instance, organization_name=None):
        super(UpdateInfraOrganizationName, self).__init__(instance)
        self.organization_name = organization_name

    @property
    def is_valid(self):
        if self.organization_name:
            return True
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return

        self.provider.update_database_organization(
            self.infra, self.organization_name)
