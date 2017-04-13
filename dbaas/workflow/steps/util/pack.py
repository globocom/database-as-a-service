# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command
from dbaas_cloudstack.models import HostAttr, CloudStackPack
from maintenance.models import DatabaseResize
from workflow.steps.util.base import BaseInstanceStep


class PackStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PackStep, self).__init__(instance)

        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

        self.database = self.instance.databaseinfra.databases.first()

    @property
    def script_variables(self):
        variables = {
            'CONFIGFILE': True,
            'IS_HA': self.instance.databaseinfra.plan.is_ha,
            'HOSTADDRESS': self.instance.address,
            'PORT': self.instance.port,
            'DBPASSWORD': self.instance.databaseinfra.password,
            'HAS_PERSISTENCE': self.instance.databaseinfra.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only
        }

        variables.update(self.get_variables_specifics())
        return variables

    def get_variables_specifics(self):
        return {}

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class Configure(PackStep):

    def __init__(self, instance):
        super(Configure, self).__init__(instance)

        self.pack = CloudStackPack.objects.get(
            offering__serviceofferingid=self.database.offering_id,
            offering__region__environment=self.database.environment,
            engine_type__name=self.database.engine_type
        )

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
