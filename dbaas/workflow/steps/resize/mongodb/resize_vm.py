# -*- coding: utf-8 -*-
import logging
from workflow.steps.base import BaseStep
from dbaas_cloudstack.models import HostAttr, DatabaseInfraOffering
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import exec_remote_command, get_credentials_for, check_ssh
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack


LOG = logging.getLogger(__name__)


class ResizeVM(BaseStep):
    def __unicode__(self):
        return "Resizing VMs..."
    
    def do(self, workflow_dict):
        try:

            database = workflow_dict['database']
            cloudstackpack = workflow_dict['cloudstackpack']
            instances_detail = workflow_dict['instances_detail']
            environment = workflow_dict['environment']
            
            cs_credentials = get_credentials_for(environment = environment, credential_type = CredentialType.CLOUDSTACK)
            cs_provider = CloudStackProvider(credentials = cs_credentials)
            
            serviceofferingid = cloudstackpack.offering.serviceofferingid

            for instance_detail in instances_detail:
                instance = instance_detail['instance']
                host = instance.hostname
                host_csattr = HostAttr.objects.get(host=host)
                offering_changed = cs_provider.change_service_for_vm(vm_id = host_csattr.vm_id, serviceofferingid = serviceofferingid)
                if not offering_changed:
                    raise Exception, "Could not change offering for Host {}".format(host)
                instance_detail['offering_changed'] = True

            LOG.info('Updating offering DatabaseInfra.')
            databaseinfraoffering = DatabaseInfraOffering.objects.get(databaseinfra = database.databaseinfra)                
            databaseinfraoffering.offering = cloudstackpack.offering
            databaseinfraoffering.save()

            return True
        except Exception, e:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
    
    def undo(self, workflow_dict):
        try:
            database = workflow_dict['database']
            original_cloudstackpack = workflow_dict['original_cloudstackpack']
            instances_detail = workflow_dict['instances_detail']
            environment = workflow_dict['environment']
            
            cs_credentials = get_credentials_for(environment = environment, credential_type = CredentialType.CLOUDSTACK)
            cs_provider = CloudStackProvider(credentials = cs_credentials)
            
            original_serviceofferingid = original_cloudstackpack.offering.serviceofferingid

            for instance_detail in instances_detail:
                if instance_detail['offering_changed']:
                    instance = instance_detail['instance']
                    host = instance.hostname
                    host_csattr = HostAttr.objects.get(host=host)
                    offering_changed = cs_provider.change_service_for_vm(vm_id = host_csattr.vm_id, serviceofferingid = original_serviceofferingid)
                    if not offering_changed:
                        raise Exception, "Could not change offering for Host {}".format(host)
                else:
                    LOG.info('No resize to instance {}'.format(instance))
                    
            LOG.info('Updating offering DatabaseInfra.')
            databaseinfraoffering = DatabaseInfraOffering.objects.get(databaseinfra = database.databaseinfra)                
            databaseinfraoffering.offering = original_cloudstackpack.offering
            databaseinfraoffering.save()

            return True
        except Exception, e:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False