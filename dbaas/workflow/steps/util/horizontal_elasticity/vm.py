# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_cloudstack.models import PlanAttr
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from workflow.steps.util.base import BaseInstanceStep

LOG = logging.getLogger(__name__)


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)

        self.databaseinfra = self.instance.databaseinfra
        self.environment = self.databaseinfra.environment
        self.plan = self.databaseinfra.plan
        self.driver = self.databaseinfra.get_driver()

        self.cs_credentials = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.CLOUDSTACK)

        self.cs_provider = CloudStackProvider(credentials=self.cs_credentials)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateVirtualMachine(VmStep):

    def __unicode__(self):
        return "Creating virtualmachine..."

    def create_host(self, address):
        from physical.models import Host

        host = Host()
        host.address = address
        host.hostname = host.address
        host.save()
        return host

    def create_host_attr(self, host, vm_id):
        from dbaas_cloudstack.models import HostAttr

        vm_credentials = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.VM)
        host_attr = HostAttr()
        host_attr.vm_id = vm_id
        host_attr.host = host
        host_attr.vm_user = vm_credentials.user
        host_attr.vm_password = vm_credentials.password
        host_attr.save()

    def create_instance(self, host):
        self.instance.hostname = host
        self.instance.address = host.address
        self.instance.port = self.driver.get_default_database_port()
        self.instance.instance_type = self.driver.get_default_instance_type()
        self.instance.save()

    def update_databaseinfra_last_vm_created(self):
        last_vm_created = self.databaseinfra.last_vm_created
        last_vm_created += 1
        self.databaseinfra.last_vm_created = last_vm_created
        self.databaseinfra.save()

    def deploy_vm(self):
        offering = self.databaseinfra.cs_dbinfra_offering.get().offering
        LOG.info("VM : {}".format(self.instance.vm_name))
        cs_plan = PlanAttr.objects.get(plan=self.plan)
        bundle = cs_plan.bundle.first()

        vm = self.cs_provider.deploy_virtual_machine(
            offering=offering.serviceofferingid,
            bundle=bundle,
            project_id=self.cs_credentials.project,
            vmname=self.instance.vm_name,
            affinity_group_id=self.cs_credentials.get_parameter_by_name(
                'affinity_group_id'),
        )

        if not vm:
            raise Exception("CloudStack could not create the virtualmachine")

        address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
        vm_id = vm['virtualmachine'][0]['id']

        return address, vm_id

    def do(self):
        LOG.info('Creating virtualmachine {}'.format(self.instance))
        address, vm_id = self.deploy_vm()

        host = self.create_host(address=address)
        self.create_host_attr(host=host, vm_id=vm_id)
        self.create_instance(host=host)
        self.update_databaseinfra_last_vm_created()

    def undo(self):
        from django.core.exceptions import ObjectDoesNotExist
        from dbaas_cloudstack.models import HostAttr

        LOG.info('Running undo of CreateVirtualMachine')

        try:
            host = self.instance.hostname
        except ObjectDoesNotExist:
            return

        host_attr = HostAttr.objects.get(host=host)

        self.cs_provider.destroy_virtual_machine(
            project_id=self.cs_credentials.project,
            environment=self.environment,
            vm_id=host_attr.vm_id)

        host_attr.delete()
        self.instance.delete()
        host.delete()
