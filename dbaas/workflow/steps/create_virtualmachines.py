# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from dbaas_cloudstack.models import PlanAttr, HostAttr, DatabaseInfraAttr
from physical.models import Host, Instance

LOG = logging.getLogger(__name__)



class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Provisioning virtualmachines..."

    def do(self, workflow_dict):

        try:
            if not 'environment' in workflow_dict and not 'plan' in workflow_dict:
                return False

            cs_credentials = get_credentials_for(environment= workflow_dict['environment'], credential_type= CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials= cs_credentials)

            cs_plan_attrs = PlanAttr.objects.get(plan=workflow_dict['plan'])

            workflow_dict['hosts'] = []
            workflow_dict['Instances'] = []
            workflow_dict['databaseinfraattr'] = []


            for vm_name in workflow_dict['names']['vms']:
                vm = cs_provider.deploy_virtual_machine( planattr= cs_plan_attrs,
            					     project_id= cs_credentials.project_id,
            					     vmname= vm_name,)

                if not vm:
                    return False

                host = Host()
                host.address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
                host.hostname= host.address
                host.cloud_portal_host = True
                host.save()
                LOG.info("Host created!")
                workflow_dict['hosts'].append(host)

                host_attr = HostAttr()
                host_attr.vm_id = vm['_id']
                host_attr.vm_user = cs_credentials.user
                host_attr.vm_password = cs_credentials.password
                host_attr.host = host
                host_attr.save()
                LOG.info("Host attrs custom attributes created!")

                instance=Instance()
                instance.address=host.address
                instance.port = 3306
                instance.is_active = True
                instance.is_arbiter = False
                instance.hostname = host
                instance.save()
                LOG.info("Instance created!")
                workflow_dict['Instances'].append(instance)

                if not len(workflow_dict['names']['vms']) > 1:
                    return True

                total = DatabaseInfraAttr.objects.filter(databaseinfra=workflow_dict['databaseinfra']).count()
                databaseinfraattr = DatabaseInfraAttr()

    	    if total == 0:
       	        databaseinfraattr.is_write = True
    	    else:
    		databaseinfraattr.is_write = False

    	    reserved_ip= cs_provider.reserve_ip(project_id= cs_credentials.project_id, vm_id=host.vm_id)
    	    if  not reserved_ip:
                    return False

    	    databaseinfraattr.ip = reserved_ip['secondary_ip']
    	    databaseinfraattr.cs_ip_id = reserved_ip['cs_ip_id']
    	    databaseinfraattr.databaseinfra = workflow_dict['databaseinfra']
    	    databaseinfraattr.save()
    	    workflow_dict['databaseinfraattr'].append(databaseinfraattr)

            return True
        except Exception,e :
            print e
            return False




    def undo(self, workflow_dict):
        try:
            if not 'databaseinfra' in workflow_dict and not 'hosts' in  workflow_dict:
                return False

            databaseinfraattr = DatabaseInfraAttr.objects.filter(databaseinfra= workflow_dict['databaseinfra'])
            cs_credentials = get_credentials_for(environment= workflow_dict['environment'], credential_type= CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials= cs_credentials)

            cs_plan_attrs = PlanAttr.objects.get(plan=workflow_dict['plan'])

            for infra_attr in databaseinfraattr:
                if not cs_provider.remove_secondary_ips(infra_attr.cs_ip_id):
                    return False

                infra_attr.delete()

            for instance in workflow_dict['databaseinfra'].instances.all():
                host = instance.hostname

                host_attr = HostAttr.objects.get(host= host)

                cs_provider.destroy_virtual_machine(project_id= cs_plan_attrs.project_id,
                                                                     environment=workflow_dict['environment'],
                                                                     vm_id= host_attr.vm_id)

                host_attr.delete()
                instance.delete()
                host.delete()

            return True
        except Exception, e:
            print e
            return False
