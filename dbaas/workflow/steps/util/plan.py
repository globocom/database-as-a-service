# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command, get_credentials_for
from dbaas_cloudstack.models import HostAttr, PlanAttr
from dbaas_credentials.models import CredentialType
from dbaas_nfsaas.models import HostAttr as HostAttrNfsaas
from workflow.steps.util.base import BaseInstanceStep
from physical.configurations import configuration_factory
import logging

LOG = logging.getLogger(__name__)


class PlanStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PlanStep, self).__init__(instance)

        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

        try:
            self.host_nfs = HostAttrNfsaas.objects.get(
                host=self.host, is_active=True
            )
        except HostAttrNfsaas.DoesNotExist:
            self.host_nfs = None

        self.infra = self.instance.databaseinfra
        self.database = self.infra.databases.first()
        self.engine = self.infra.engine
        self.environment = self.infra.environment
        self.disk_offering = self.infra.disk_offering

        self.plan = self.infra.plan
        self.cs_plan = PlanAttr.objects.get(plan=self.plan)

    def get_equivalent_plan(self):
        self.plan = self.infra.plan.engine_equivalent_plan
        self.cs_plan = PlanAttr.objects.get(plan=self.plan)

    @property
    def script_variables(self):
        variables = {
            'DATABASENAME': self.database.name,
            'DBPASSWORD': self.infra.password,
            'HOST': self.host.hostname.split('.')[0],
            'ENGINE': self.plan.engine.engine_type.name,
            'UPGRADE': True,
            'IS_HA': self.plan.is_ha,
            'IS_READ_ONLY': self.instance.read_only,
            'DISK_SIZE_IN_GB': self.disk_offering.size_gb(),
            'ENVIRONMENT': self.environment
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

    def get_configuration(self):
        current_resize = self.database.resizes.last()
        if current_resize and current_resize.is_running:
            offering = current_resize.target_offer.offering
        else:
            offering = self.cs_plan.get_stronger_offering()

        try:
            configuration = configuration_factory(
                self.engine.name, offering.memory_size_mb
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
        return_code = exec_remote_command(
            self.host.address, self.host_cs.vm_user, self.host_cs.vm_password,
            script, output
        )

        if return_code != 0:
            raise EnvironmentError(
                'Could not execute script {}: {}'.format(
                    return_code, output
                )
            )


class Initialization(PlanStep):

    def __unicode__(self):
        return "Executing plan initial script..."

    def do(self):
        self.run_script(self.cs_plan.initialization_script)


class Configure(PlanStep):

    def __unicode__(self):
        return "Executing plan configure script..."

    def do(self):
        self.run_script(self.cs_plan.configuration_script)


class InitializationForUpgrade(Initialization):
    def __init__(self, instance):
        super(InitializationForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureForUpgrade(Configure):
    def __init__(self, instance):
        super(ConfigureForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class InitializationMongoHA(Initialization):

    def get_variables_specifics(self):
        database_rule = 'SECONDARY'
        if self.instance.instance_type == self.instance.MONGODB_ARBITER:
            database_rule = 'ARBITER'

        return {
            'DATABASERULE': database_rule
        }


class ConfigureMongoHA(Configure):

    def get_variables_specifics(self):
        return {
            'REPLICASETNAME': self.infra.get_driver().get_replica_name(),
            'MONGODBKEY': self.infra.database_key
        }


class InitializationMongoHAForUpgrade(InitializationMongoHA):
    def __init__(self, instance):
        super(InitializationMongoHAForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureMongoHAForUpgrade(ConfigureMongoHA):
    def __init__(self, instance):
        super(ConfigureMongoHAForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


def redis_instance_parameter(host):
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


def sentinel_instance_parameter(host):
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


class InitializationRedis(Initialization):

    def get_variables_specifics(self):
        return redis_instance_parameter(self.host)


class ConfigureRedis(Configure):

    def get_variables_specifics(self):
        master = self.infra.get_driver().get_master_instance()

        variables = {
            'SENTINELMASTER': master.address,
            'SENTINELMASTERPORT': master.port,
            'MASTERNAME': self.infra.name,
        }
        variables.update(redis_instance_parameter(self.host))
        variables.update(sentinel_instance_parameter(self.host))

        return variables


class InitializationRedisForUpgrade(InitializationRedis):
    def __init__(self, instance):
        super(InitializationRedisForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()


class ConfigureRedisForUpgrade(ConfigureRedis):
    def __init__(self, instance):
        super(ConfigureRedisForUpgrade, self).__init__(instance)
        self.get_equivalent_plan()
