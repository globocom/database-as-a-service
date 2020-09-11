# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command_host, \
    get_credentials_for
from dbaas_credentials.models import CredentialType
from base import BaseInstanceStep, BaseInstanceStepMigration
from physical.configurations import configuration_factory
from physical.models import Offering, Volume
from system.models import Configuration
import logging

LOG = logging.getLogger(__name__)


class PlanStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PlanStep, self).__init__(instance)
        self._pack = None
        self.run_script_host = self.host

    @property
    def host_nfs(self):
        try:
            return Volume.objects.get(host=self.host, is_active=True)
        except Volume.DoesNotExist:
            return None

    @property
    def script_variables(self):
        variables = {
            'DATABASENAME': self.database.name,
            'DBPASSWORD': self.infra.password,
            'HOST': self.host.hostname.split('.')[0],
            'HOSTADDRESS': self.instance.address,
            'ENGINE': self.plan.engine.engine_type.name,
            'MOVE_DATA': (
                bool(self.upgrade) or
                bool(self.reinstall_vm) or
                bool(self.engine_migration)
            ),
            'DRIVER_NAME': self.infra.get_driver().topology_name(),
            # TODO: Remove that when VP is ready
            'DISK_SIZE_IN_GB': self.disk_offering.size_gb()if self.disk_offering else 8,
            'ENVIRONMENT': self.environment,
            'HAS_PERSISTENCE': self.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
            'SSL_CONFIGURED': self.infra.ssl_configured,
            'SSL_MODE_ALLOW': self.infra.ssl_mode == self.infra.ALLOWTLS,
            'SSL_MODE_PREFER': self.infra.ssl_mode == self.infra.PREFERTLS,
            'SSL_MODE_REQUIRE': self.infra.ssl_mode == self.infra.REQUIRETLS,
        }

        if self.infra.ssl_configured:
            from workflow.steps.util.ssl import InfraSSLBaseName
            from workflow.steps.util.ssl import InstanceSSLBaseName
            infra_ssl = InfraSSLBaseName(self.instance)
            instance_ssl = InstanceSSLBaseName(self.instance)
            variables['INFRA_SSL_CA'] = infra_ssl.ca_file_path
            variables['INFRA_SSL_CERT'] = infra_ssl.cert_file_path
            variables['INFRA_SSL_KEY'] = infra_ssl.key_file_path
            variables['MASTER_SSL_CA'] = infra_ssl.master_ssl_ca
            variables['INSTANCE_SSL_CA'] = instance_ssl.ca_file_path
            variables['INSTANCE_SSL_CERT'] = instance_ssl.cert_file_path
            variables['INSTANCE_SSL_KEY'] = instance_ssl.key_file_path

        variables['configuration'] = self.get_configuration()

        variables.update(self.get_variables_specifics())
        return variables

    def get_log_endpoint(self):
        if Configuration.get_by_name_as_int('graylog_integration') == 1:
            credential = get_credentials_for(
                environment=self.environment,
                credential_type=CredentialType.GRAYLOG
            )
        elif Configuration.get_by_name_as_int('kibana_integration') == 1:
            credential = get_credentials_for(
                environment=self.environment,
                credential_type=CredentialType.KIBANA_LOG
            )
        else:
            return ""
        return credential.get_parameter_by_name('endpoint_log')

    @property
    def offering(self):
        if self.resize:
            return self.resize.target_offer

        try:
            return self.infra.offering
        except Offering.DoesNotExist:
            return self.instance.offering

    def get_configuration(self):
        try:
            configuration = configuration_factory(
                self.infra, self.offering.memory_size_mb
            )
        except NotImplementedError:
            return None
        else:
            return configuration

    def get_variables_specifics(self):
        return {}

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def run_script(self, plan_script):
        script = build_context_script(self.script_variables, plan_script)
        output = {}
        return_code = exec_remote_command_host(
            self.run_script_host, script, output
        )
        if return_code != 0:
            raise EnvironmentError(
                'Could not execute script {}: {}'.format(
                    return_code, output
                )
            )

        return output


class PlanStepNewInfra(PlanStep):

    @property
    def database(self):
        from logical.models import Database
        if self.infra.databases.exists():
            return self.infra.databases.first()
        database = Database()
        step_manager = self.infra.databases_create.last()
        database.name = (step_manager.name
                         if step_manager else self.step_manager.name)
        return database


class PlanStepNewInfraSentinel(PlanStepNewInfra):

    @property
    def is_valid(self):
        return self.instance.is_sentinel

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        base = super(PlanStepNewInfraSentinel, self).get_variables_specifics()
        base.update(driver.master_parameters(
            self.instance, self.infra.instances.first()
        ))
        return base


class PlanStepRestore(PlanStep):

    @property
    def host_nfs(self):
        try:
            return Volume.objects.filter(
                host=self.host, is_active=False
            ).last()
        except Volume.DoesNotExist:
            return None

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        base = super(PlanStepRestore, self).get_variables_specifics()
        if self.restore.is_master(self.instance) or self.restore.is_slave(self.instance):
            base.update(driver.master_parameters(
                self.instance, self.restore.master_for(self.instance)
            ))
        return base


class PlanStepUpgrade(PlanStep):

    @property
    def plan(self):
        plan = super(PlanStepUpgrade, self).plan
        return plan.engine_equivalent_plan


class PlanStepMigrateEngine(PlanStep):

    @property
    def plan(self):
        plan = super(PlanStepMigrateEngine, self).plan
        return plan.migrate_engine_equivalent_plan


class Initialization(PlanStep):

    def __unicode__(self):
        return "Executing plan initial script..."

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.initialization_parameters(self.instance)

    def do(self):
        if self.is_valid:
            self.run_script(self.plan.script.initialization_template)


class Configure(PlanStep):

    def __unicode__(self):
        return "Executing plan configure script..."

    @property
    def extra_variables(self):
        return {}

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.configuration_parameters(self.instance, **self.extra_variables)

    def do(self):
        if self.is_valid:
            self.run_script(self.plan.script.configuration_template)


class ConfigureDatabaseFile(Configure):

    @property
    def extra_variables(self):
        return {
            'CONFIGFILE_ONLY': True,
            'CONFIG_FILE_PATH': '/tmp/database_configuration_file'
        }


class StartReplication(PlanStep):

    def __unicode__(self):
        return "Executing replication start script..."

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.start_replication_parameters(self.instance)

    def do(self):
        if self.is_valid:
            self.run_script(self.plan.script.start_replication_template)


class StartReplicationFirstNode(StartReplication):

    @property
    def is_valid(self):
        base = super(StartReplication, self).is_valid
        if not base:
            return base

        return self.instance == self.infra.instances.first()


class InitializationForUpgrade(Initialization, PlanStepUpgrade):
    pass


class InitializationForMigrateEngine(Initialization, PlanStepMigrateEngine):
    pass


class ConfigureForUpgrade(Configure, PlanStepUpgrade):
    @property
    def extra_variables(self):
        return {'need_master': True}


class ConfigureForMigrateEngine(Configure, PlanStepMigrateEngine):
    pass


class InitializationForNewInfra(Initialization, PlanStepNewInfra):
    pass


class ConfigureForNewInfra(Configure, PlanStepNewInfra):
    pass


class ConfigureLog(Configure):

    def __unicode__(self):
        return "Configuring Log..."

    @property
    def extra_variables(self):
        return {'LOG_ENDPOINT': self.get_log_endpoint()}

    def do(self):
        if self.is_valid:
            self.run_script(self.plan.script.configure_log_template)


class ConfigureLogForNewInfra(ConfigureLog, PlanStepNewInfra):
    pass


class ConfigureLogMigrateEngine(ConfigureLog, PlanStepMigrateEngine):
    pass


class StartReplicationNewInfra(StartReplication, PlanStepNewInfra):
    pass


class StartReplicationFirstNodeNewInfra(
    StartReplicationFirstNode, PlanStepNewInfra
):
    pass


class InitializationForNewInfraSentinel(
    PlanStepNewInfraSentinel, Initialization
):
    pass


class ConfigureForNewInfraSentinel(PlanStepNewInfraSentinel, Configure):
    pass


class ConfigureSentinelFile(ConfigureForNewInfraSentinel):

    @property
    def extra_variables(self):
        return {
            'ONLY_SENTINEL': True,
            'CONFIG_FILE_PATH': '/tmp/sentinel_configuration_file'
        }


class ConfigureForResizeLog(Configure):

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        base = driver.configuration_parameters_for_log_resize(self.instance)
        base.update({'CONFIGFILE_ONLY': True})
        return base


class InitializationMigration(Initialization, BaseInstanceStepMigration):

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.initialization_parameters(self.instance.future_instance)

    @property
    def offering(self):
        offering_base = self.infra.cs_dbinfra_offering.get().offering
        return offering_base.equivalent_offering


class ConfigureMigration(Configure, BaseInstanceStepMigration):

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.configuration_parameters_migration(
            self.instance.future_instance
        )

    @property
    def offering(self):
        offering_base = self.infra.cs_dbinfra_offering.get().offering
        return offering_base.equivalent_offering


class ConfigureRestore(PlanStepRestore, Configure):

    def __init__(self, instance, **kwargs):
        super(ConfigureRestore, self).__init__(instance)
        self.kwargs = kwargs

    def get_variables_specifics(self):
        base = super(ConfigureRestore, self).get_variables_specifics()

        base.update(self.kwargs)
        base['CONFIGFILE_ONLY'] = True,
        base['CREATE_SENTINEL_CONFIG'] = True

        driver = self.infra.get_driver()

        if self.restore.is_master(self.instance) or self.restore.is_slave(self.instance):
            base.update(driver.master_parameters(
                self.instance, self.restore.master_for(self.instance)
            ))

        return base

class ConfigureOnlyDBConfigFile(Configure):
    def get_variables_specifics(self):
        base = super(ConfigureOnlyDBConfigFile, self).get_variables_specifics()
        base.update({'CONFIGFILE_ONLY': True})
        return base


class ConfigureForUpgradeOnlyDBConfigFile(ConfigureOnlyDBConfigFile, PlanStepUpgrade):
    pass


class ResizeConfigure(ConfigureOnlyDBConfigFile):

    def do(self):
        self._pack = self.resize.target_offer
        super(ResizeConfigure, self).do()

    def undo(self):
        self._pack = self.resize.source_offer
        super(ResizeConfigure, self).undo()

class ConfigureForChangePersistence(ConfigureOnlyDBConfigFile):

    @property
    def change_persistence(self):
        persistence = self.database.change_persistence.last()
        if persistence and persistence.is_running:
            return persistence
        raise EnvironmentError(
            "There is not any 'Change Persistence Maintenance' running."
        )

    @property
    def plan(self):
        return self.change_persistence.target_plan

    def get_configuration(self):
        infra = self.infra
        infra.plan = self.plan
        configuration = configuration_factory(
            infra, self.offering.memory_size_mb
        )
        return configuration


class ConfigureWithoutSSL(Configure):

    def get_variables_specifics(self):
        base = super(ConfigureWithoutSSL, self).get_variables_specifics()
        base['SSL_CONFIGURED'] = False
        base['SSL_MODE_ALLOW'] = False
        base['SSL_MODE_PREFER'] = False
        base['SSL_MODE_REQUIRE'] = False
        return base