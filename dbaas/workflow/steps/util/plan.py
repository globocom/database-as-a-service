# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command_host, \
    get_credentials_for
from dbaas_cloudstack.models import HostAttr, PlanAttr
from dbaas_cloudstack.models import CloudStackPack
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr as HostAttrNfsaas
from base import BaseInstanceStep, BaseInstanceStepMigration
from physical.configurations import configuration_factory
import logging

LOG = logging.getLogger(__name__)


class PlanStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PlanStep, self).__init__(instance)
        self.pack = CloudStackPack.objects.get(
            offering__serviceofferingid=self.database.offering_id,
            offering__region__environment=self.environment,
            engine_type__name=self.database.engine_type
        )

    @property
    def cs_plan(self):
        return PlanAttr.objects.get(plan=self.plan)

    @property
    def host_cs(self):
        return HostAttr.objects.get(host=self.host)

    @property
    def host_nfs(self):
        try:
            return HostAttrNfsaas.objects.get(host=self.host, is_active=True)
        except HostAttrNfsaas.DoesNotExist:
            return None

    @property
    def script_variables(self):
        variables = {
            'DATABASENAME': self.database.name,
            'DBPASSWORD': self.infra.password,
            'HOST': self.host.hostname.split('.')[0],
            'ENGINE': self.plan.engine.engine_type.name,
            'UPGRADE': True,
            'DRIVER_NAME': self.infra.get_driver().topology_name(),
            'IS_READ_ONLY': self.instance.read_only,
            'DISK_SIZE_IN_GB': self.disk_offering.size_gb(),
            'ENVIRONMENT': self.environment,
            'HAS_PERSISTENCE': self.infra.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
        }

        variables['configuration'] = self.get_configuration()
        variables['GRAYLOG_ENDPOINT'] = self.get_graylog_config()
        if self.host_nfs:
            variables['EXPORTPATH'] = self.host_nfs.nfsaas_path

        variables.update(self.get_variables_specifics())
        return variables

    def get_graylog_config(self):
        credential = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.GRAYLOG
        )
        return credential.get_parameter_by_name('endpoint_log')

    @property
    def offering(self):
        if self.resize:
            return self.resize.target_offer.offering

        return self.pack.offering

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
        return_code = exec_remote_command_host(self.host, script, output)
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
        database = Database()
        database.name = self.infra.databases_create.last().name
        return database


class PlanStepRestore(PlanStep):

    @property
    def host_nfs(self):
        try:
            return HostAttrNfsaas.objects.filter(
                host=self.host, is_active=False
            ).last()
        except HostAttrNfsaas.DoesNotExist:
            return None


class PlanStepUpgrade(PlanStep):

    @property
    def plan(self):
        plan = super(PlanStepUpgrade, self).plan
        return plan.engine_equivalent_plan


class Initialization(PlanStep):

    def __unicode__(self):
        return "Executing plan initial script..."

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.initialization_parameters(self.instance)

    def do(self):
        self.run_script(self.plan.script.initialization_template)


class Configure(PlanStep):

    def __unicode__(self):
        return "Executing plan configure script..."

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.configuration_parameters(self.instance)

    def do(self):
        self.run_script(self.plan.script.configuration_template)


class InitializationForUpgrade(Initialization, PlanStepUpgrade):
    pass


class ConfigureForUpgrade(Configure, PlanStepUpgrade):
    pass


class InitializationForNewInfra(Initialization, PlanStepNewInfra):
    pass


class ConfigureForNewInfra(Configure, PlanStepNewInfra):
    pass


class InitializationRestore(Initialization, PlanStepRestore):
    pass


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


class ConfigureRestore(Configure):

    def __init__(self, instance, **kwargs):
        super(ConfigureRestore, self).__init__(instance)
        self.kwargs = kwargs

    def get_variables_specifics(self):
        base = super(ConfigureRestore, self).get_variables_specifics()
        base.update(self.kwargs)
        base.update({'CONFIGFILE_ONLY': True,
                    'CREATE_SENTINEL_CONFIG': True})
        LOG.info(base)
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
        self.pack = self.resize.target_offer
        super(ResizeConfigure, self).do()

    def undo(self):
        self.pack = self.resize.source_offer
        super(ResizeConfigure, self).undo()
