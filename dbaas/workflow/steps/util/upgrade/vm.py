# -*- coding: utf-8 -*-
from util import check_ssh
from dbaas_cloudstack.models import HostAttr, PlanAttr
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from workflow.steps.util.base import BaseInstanceStep


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)

        integration = CredentialType.objects.get(type=CredentialType.CLOUDSTACK)
        environment = self.instance.databaseinfra.environment
        credentials = Credential.get_credentials(environment, integration)

        self.provider = CloudStackProvider(credentials=credentials)
        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

        new_plan = self.instance.databaseinfra.plan.engine_equivalent_plan
        cs_plan = PlanAttr.objects.get(plan=new_plan)
        self.bundle = cs_plan.bundle.first()

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class Stop(VmStep):

    def __unicode__(self):
        return "Stopping VM..."

    def do(self):
        stopped = self.provider.stop_virtual_machine(self.host_cs.vm_id)
        if not stopped:
            raise EnvironmentError("Could not stop VM")


class Start(VmStep):

    def __unicode__(self):
        return "Starting VM..."

    def do(self):
        started = self.provider.start_virtual_machine(self.host_cs.vm_id)
        if not started:
            raise EnvironmentError("Could not start VM")

class InstallNewTemplate(VmStep):

    def __unicode__(self):
        return "Installing new template to VM..."

    def do(self):
        reinstall = self.provider.reinstall_new_template(
            self.host_cs.vm_id, self.bundle.templateid
        )
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class WaitingBeReady(VmStep):

    def __unicode__(self):
        return "Waiting for VM be ready..."

    def do(self):
        host_ready = check_ssh(
            self.host.address, self.host_cs.vm_user,
            self.host_cs.vm_password, wait=5, interval=10
        )
        if not host_ready:
            raise EnvironmentError('VM is not ready')


class UpdateOSDescription(VmStep):

    def __unicode__(self):
        return "Updating instance OS description..."

    def do(self):
        self.instance.hostname.update_os_description()
