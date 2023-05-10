# -*- coding: utf-8 -*-
import logging
import requests
from dbaas_dbmonitor.provider import DBMonitorProvider
from workflow.steps.util.base import BaseInstanceStep
from system.models import Configuration as conf

LOG = logging.getLogger(__name__)


class DBMonitorStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DBMonitorStep, self).__init__(instance)
        self.provider = DBMonitorProvider()

    @property
    def dbmonitor_database_id(self):
        url = conf.get_by_name('dbmonitor_url_get_database_id').format(self.infra.name)
        database_id = None
        response = requests.get(url)
        if response.status_code == 200:
            ### Raise an exception when api returns more than one dbmonitor_database object
            if len(response.json()) > 1:
                raise Exception('Teste exception')
            database_id = response.json()[0].get('id')
        return database_id

    def _enable_monitoring(self):
        status = True
        url = conf.get_by_name('dbmonitor_url_activate_monitoring').format(self.dbmonitor_database_id)
        response = requests.get(url)
        if response.status_code != 200:
            status = False
        return status
        # self.provider.enabled_dbmonitor_monitoring_instance(self.instance)

    def _disable_monitoring(self):
        status = True
        url = conf.get_by_name('dbmonitor_url_deactivate_monitoring').format(self.dbmonitor_database_id)
        response = requests.get(url)
        if response.status_code != 200:
            status = False
        return status
        # self.provider.disabled_dbmonitor_monitoring_instance(self.instance)

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


class DisableMonitoringTemporaryInstance(DisableMonitoring):
    
    @property
    def is_valid(self):
        return self.instance.temporary
    
    def do(self):
        if not self.is_valid:
            return
        
        return super(DisableMonitoringTemporaryInstance, self).do()


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


class CreateMonitoringTemporaryInstance(CreateMonitoring):

    @property
    def is_valid(self):
        if not self.instance.temporary:
            return False
        return super(CreateMonitoringTemporaryInstance, self).is_valid
    
    def do(self):
        if self.is_valid:
            return super(CreateMonitoringTemporaryInstance, self).do()


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

    def undo(self):
        self.provider.update_database_cloud(
            self.infra, self.infra.environment.cloud.name)


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
