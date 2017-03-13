# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_cloudstack.models import PlanAttr
from dbaas_credentials.credential import Credential
from dbaas_credentials.models import CredentialType
from workflow.steps.util.base import BaseInstanceStep

LOG = logging.getLogger(__name__)


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)

        self.databaseinfra = self.instance.databaseinfra
        self.environment = self.databaseinfra.environment
        self.plan = self.databaseinfra.plan

        integration = CredentialType.objects.get(
            type=CredentialType.CLOUDSTACK)
        self.cs_credentials = Credential.get_credentials(
            self.environment, integration)
        self.cs_provider = CloudStackProvider(credentials=self.cs_credentials)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateVirtualMachine(VmStep):

    def __unicode__(self):
        return "Creating virtualmachine..."

    def do(self):
        LOG.info('Creating virtualmachine for'.format(self.instance.databaseinfra))
        last_vm_created = self.databaseinfra.last_vm_created
        last_vm_created += 1
        hostname = "%s-0%i-%s" % (self.databaseinfra.name_prefix,
                                  last_vm_created,
                                  self.databaseinfra.name_stamp)
        LOG.info("Hostname={}".format(hostname))
        self.databaseinfra.last_vm_created = last_vm_created
        self.databaseinfra.save()
        return

        offering = self.databaseinfra.cs_dbinfra_offering.get().offering
        vm_name = 'db02-04-148899273204'
        cs_plan = PlanAttr.objects.get(plan=self.plan)
        bundle = cs_plan.bundle.first()

        vm = self.cs_provider.deploy_virtual_machine(
            offering=offering.serviceofferingid,
            bundle=bundle,
            project_id=self.cs_credentials.project,
            vmname=vm_name,
            affinity_group_id=self.cs_credentials.get_parameter_by_name('affinity_group_id'),
        )
        if not vm:
            raise Exception("CloudStack could not create the virtualmachine")
