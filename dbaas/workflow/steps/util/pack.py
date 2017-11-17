# -*- coding: utf-8 -*-
from util import build_context_script, exec_remote_command, get_credentials_for
from dbaas_cloudstack.models import HostAttr, CloudStackPack, PlanAttr
from dbaas_credentials.models import CredentialType
from physical.configurations import configuration_factory
from base import BaseInstanceStep


class PackStep(BaseInstanceStep):

    def __init__(self, instance):
        super(PackStep, self).__init__(instance)
        self.pack = CloudStackPack.objects.get(
            offering__serviceofferingid=self.database.offering_id,
            offering__region__environment=self.environment,
            engine_type__name=self.database.engine_type
        )

    @property
    def host_cs(self):
        return HostAttr.objects.get(host=self.host)

    @property
    def cs_plan(self):
        return PlanAttr.objects.get(plan=self.plan)

    @property
    def script_variables(self):
        variables = {
            'CONFIGFILE': True,
            'DRIVER_NAME': self.infra.get_driver().topology_name(),
            'HOSTADDRESS': self.instance.address,
            'PORT': self.instance.port,
            'DBPASSWORD': self.infra.password,
            'HAS_PERSISTENCE': self.infra.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
            'DISK_SIZE_IN_GB': self.disk_offering.size_gb(),
            'ENVIRONMENT': self.environment,
            'ENGINE_VERSION': self.engine.version,
        }

        variables['configuration'] = self.get_configuration()
        variables['GRAYLOG_ENDPOINT'] = self.get_graylog_config()

        variables.update(self.get_variables_specifics())
        return variables

    def get_graylog_config(self):
        credential = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.GRAYLOG
        )
        return credential.get_parameter_by_name('endpoint_log')

    def get_configuration(self):
        try:
            configuration = configuration_factory(
                self.infra, self.pack.offering.memory_size_mb
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
        self.do()


class Configure(PackStep):

    def __unicode__(self):
        return "Executing pack script..."

    def get_variables_specifics(self):
        driver = self.infra.get_driver()
        return driver.configuration_parameters(self.instance)

    def do(self):
        script = build_context_script(
            self.script_variables, self.pack.script_template
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

    def do(self):
        self.pack = self.resize.target_offer
        super(ResizeConfigure, self).do()

    def undo(self):
        self.pack = self.resize.source_offer
        super(ResizeConfigure, self).undo()
