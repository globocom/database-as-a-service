# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command
from dbaas_cloudstack.models import HostAttr, CloudStackPack, PlanAttr
from maintenance.models import DatabaseResize
from physical.configurations import configuration_factory
from workflow.steps.util.base import BaseInstanceStep


class PackStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PackStep, self).__init__(instance)

        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

        self.infra = self.instance.databaseinfra
        self.database = self.infra.databases.first()
        self.disk_offering = self.infra.disk_offering
        self.engine = self.infra.engine

        self.plan = self.infra.plan
        self.cs_plan = PlanAttr.objects.get(plan=self.plan)

        self.pack = CloudStackPack.objects.get(
            offering__serviceofferingid=self.database.offering_id,
            offering__region__environment=self.database.environment,
            engine_type__name=self.database.engine_type
        )

    @property
    def script_variables(self):
        variables = {
            'CONFIGFILE': True,
            'IS_HA': self.infra.plan.is_ha,
            'HOSTADDRESS': self.instance.address,
            'PORT': self.instance.port,
            'DBPASSWORD': self.infra.password,
            'HAS_PERSISTENCE': self.infra.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
            'DISK_SIZE_IN_GB': self.disk_offering.size_gb(),
            'ENVIRONMENT': self.infra.environment
        }

        variables['configuration'] = self.get_configuration()
        variables.update(self.get_variables_specifics())
        return variables

    def get_configuration(self):
        try:
            configuration = configuration_factory(
                self.engine.name, self.pack.offering.memory_size_mb
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


class Configure(PackStep):

    def __unicode__(self):
        return "Executing pack script..."

    def do(self):
        script = build_context_script(
            self.script_variables, self.pack.script
        )

        output = {}
        return_code = exec_remote_command(
            self.host.address, self.host_cs.vm_user, self.host_cs.vm_password,
            script, output
        )

        if return_code != 0:
            raise EnvironmentError(
                'Could not execute pack script {}: {}'.format(
                    return_code, output
                )
            )


class ResizeConfigure(Configure):

    def __init__(self, instance):
        super(ResizeConfigure, self).__init__(instance)
        self.pack = DatabaseResize.objects.last().current_to(self.database).target_offer


class ConfigureRedis(Configure):

    def get_variables_specifics(self):
        redis = self.host.database_instance()
        redis_address = ''
        redis_port = ''
        if redis:
            redis_address = redis.address
            redis_port = redis.port

        return {
            'HOSTADDRESS': redis_address,
            'PORT': redis_port,
        }
