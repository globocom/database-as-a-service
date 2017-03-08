# -*- coding: utf-8 -*-
from time import sleep
from util import check_ssh
from dbaas_cloudstack.models import HostAttr, PlanAttr
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from workflow.steps.util.base import BaseInstanceStep
from maintenance.models import DatabaseResize


CHANGE_MASTER_ATTEMPS = 4
CHANGE_MASTER_SECONDS = 15


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)

        integration = CredentialType.objects.get(
            type=CredentialType.CLOUDSTACK
        )
        environment = self.instance.databaseinfra.environment
        self.credentials = Credential.get_credentials(environment, integration)

        self.provider = CloudStackProvider(credentials=self.credentials)
        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

        self.infra = self.instance.databaseinfra
        self.driver = self.infra.get_driver()

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

    def __init__(self, instance):
        super(InstallNewTemplate, self).__init__(instance)

        target_plan = self.instance.databaseinfra.plan.engine_equivalent_plan
        cs_plan = PlanAttr.objects.get(plan=target_plan)
        self.bundle = cs_plan.bundle.first()

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


class ChangeOffering(VmStep):

    def __init__(self, instance):
        super(ChangeOffering, self).__init__(instance)

        database = self.instance.databaseinfra.databases.last()
        target_offer = DatabaseResize.current_to(database).target_offer
        self.target_offering_id = target_offer.offering.serviceofferingid

    def __unicode__(self):
        return "Resizing VM..."

    def do(self):
        cloudstack_offering_id = self.provider.get_vm_offering_id(
            vm_id=self.host_cs.vm_id,
            project_id=self.credentials.project
        )

        if not cloudstack_offering_id == self.target_offering_id:
            resized = self.provider.change_service_for_vm(
                vm_id=self.host_cs.vm_id,
                serviceofferingid=self.target_offering_id
            )
        else:
            resized = True

        if not resized:
            raise Exception("Could not change offering")


class ChangeMaster(VmStep):

    def __unicode__(self):
        return "Changing master node..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        if self.driver.check_instance_is_master(instance=self.instance):
            error = None

            for _ in range(CHANGE_MASTER_ATTEMPS):
                try:
                    self.driver.check_replication_and_switch(self.instance)
                except Exception as e:
                    error = e
                    sleep(CHANGE_MASTER_SECONDS)
                else:
                    return

            raise error
