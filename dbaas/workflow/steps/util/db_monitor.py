# -*- coding: utf-8 -*-
import logging
from dbaas_dbmonitor.provider import DBMonitorProvider
from workflow.steps.util.base import BaseInstanceStep

LOG = logging.getLogger(__name__)


class DBMonitorStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DBMonitorStep, self).__init__(instance)
        self.provider = DBMonitorProvider()

    def _enable_monitoring(self):
        self.provider.enabled_dbmonitor_monitoring_instance(self.instance)

    def _disable_monitoring(self):
        self.provider.disabled_dbmonitor_monitoring_instance(self.instance)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class EnableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Enabling DB Monitor..."

    def do(self):
        self._enable_monitoring()

    def undo(self):
        self._disable_monitoring()


class DisableMonitoring(DBMonitorStep):

    def __unicode__(self):
        return "Disabling DB Monitor..."

    def do(self):
        self._disable_monitoring()

    def undo(self):
        self._enable_monitoring()


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
        if ((self.upgrade or self.upgrade_patch or self.engine_migration) and
                self.instance == self.infra.instances.all()[0]):
            return True
        return False

    @property
    def target_version(self):
        if self.upgrade:
            return self.upgrade.target_plan.engine.full_inicial_version
        elif self.engine_migration:
            return self.engine_migration.target_plan.engine.full_inicial_version
        elif self.upgrade_patch:
            return self.upgrade_patch.target_patch_full_version

    @property
    def source_version(self):
        if self.upgrade:
            return self.upgrade.source_plan.engine.full_inicial_version
        elif self.engine_migration:
            return self.engine_migration.source_plan.engine.full_inicial_version
        elif self.upgrade_patch:
            return self.upgrade_patch.source_patch_full_version

    def do(self):
        if self.is_valid:
            self.provider.update_dbmonitor_database_version(
                self.infra, self.target_version)

    def undo(self):
        if self.is_valid:
            self.provider.update_dbmonitor_database_version(
                self.infra, self.source_version)


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

class UpdateInfraSSLMonitor(DBMonitorStep):

    def __unicode__(self):
        return "Update SSL info on DB Monitor..."

    def do(self):
        self.provider.update_database_ssl_info(self.infra)
