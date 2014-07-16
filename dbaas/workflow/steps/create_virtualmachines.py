# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from dbaas_cloudstack.models import PlanAttr, HostAttr
from physical.models import Host, Instance

LOG = logging.getLogger(__name__)


class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Creating virtualmachines..."

    def do(self, workflow_dict):

        try:
            if not 'environment' in workflow_dict and not 'plan' in workflow_dict:
                return False

            cs_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.CLOUDSTACK)

            vm_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.VM)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            cs_plan_attrs = PlanAttr.objects.get(plan=workflow_dict['plan'])

            workflow_dict['hosts'] = []
            workflow_dict['instances'] = []
            workflow_dict['databaseinfraattr'] = []
            workflow_dict['vms_id'] = []

            for index, vm_name in enumerate(workflow_dict['names']['vms']):

                vm = cs_provider.deploy_virtual_machine(
                    offering=cs_plan_attrs.serviceofferingid.all()[0].serviceofferingid,
                    bundle= cs_plan_attrs.bundle.all()[0],
                    project_id=cs_credentials.project,
                    vmname=vm_name,
                )

                if not vm:
                    return False

                LOG.debug("New virtualmachine: %s" % vm)

                workflow_dict['vms_id'].append(vm['virtualmachine'][0]['id'])

                host = Host()
                host.address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
                host.hostname = host.address
                host.cloud_portal_host = True
                host.save()
                LOG.info("Host created!")

                workflow_dict['hosts'].append(host)

                host_attr = HostAttr()
                host_attr.vm_id = vm['virtualmachine'][0]['id']
                host_attr.vm_user = vm_credentials.user
                host_attr.vm_password = vm_credentials.password
                host_attr.host = host
                host_attr.save()
                LOG.info("Host attrs custom attributes created!")

                instance = Instance()
                instance.address = host.address
                if workflow_dict['enginecod'] == workflow_dict['MYSQL']:
                    instance.port = 3306
                elif workflow_dict['enginecod'] == workflow_dict['MONGODB']:
                    instance.port = 27017
                instance.is_active = True
                if workflow_dict['enginecod'] == workflow_dict['MONGODB'] and index == 2:
                    instance.is_arbiter = True
                else:
                    instance.is_arbiter = False

                instance.hostname = host
                instance.databaseinfra = workflow_dict['databaseinfra']
                instance.save()
                LOG.info("Instance created!")

                workflow_dict['instances'].append(instance)

                if  workflow_dict['qt']==1:

                    LOG.info("Updating databaseinfra endpoint...")
                    databaseinfra = workflow_dict['databaseinfra']
                    databaseinfra.endpoint = instance.address + ":%i" %(instance.port)
                    databaseinfra.save()
                    workflow_dict['databaseinfra'] = databaseinfra

                    return True

            return True
        except Exception as e:
            print e
            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            cs_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            instances = workflow_dict['databaseinfra'].instances.all()

            if not instances:

                for vm_id in workflow_dict['vms_id']:
                    cs_provider.destroy_virtual_machine(
                    project_id=cs_credentials.project,
                    environment=workflow_dict['environment'],
                    vm_id=vm_id)


                for host in workflow_dict['hosts']:
                    host_attr = HostAttr.objects.filter(host=host)

                    host.delete()
                    LOG.info("Host deleted!")

                    if host_attr:
                        host_attr[0].delete()
                        LOG.info("HostAttr deleted!")


            for instance in instances:
                host = instance.hostname

                host_attr = HostAttr.objects.get(host=host)

                LOG.info("Destroying virtualmachine %s" % host_attr.vm_id)

                cs_provider.destroy_virtual_machine(
                    project_id=cs_credentials.project,
                    environment=workflow_dict['environment'],
                    vm_id=host_attr.vm_id)

                host_attr.delete()
                LOG.info("HostAttr deleted!")

                instance.delete()
                LOG.info("Instance deleted")

                host.delete()
                LOG.info("Host deleted!")

            return True
        except Exception as e:
            print e
            return False
