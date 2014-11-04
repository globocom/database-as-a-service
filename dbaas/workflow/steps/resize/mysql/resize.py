# -*- coding: utf-8 -*-
import logging
from workflow.steps.base import BaseStep
from logical.models import Database
from dbaas_cloudstack.models import HostAttr, DatabaseInfraOffering
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import exec_remote_command, get_credentials_for, check_ssh
import datetime
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack


LOG = logging.getLogger(__name__)


class ResizeInstance(BaseStep):
    def __unicode__(self):
        return "Resizing instances..."
    
    def do(self, workflow_dict):
        try:

            database = workflow_dict['database']
            cloudstackpack = workflow_dict['cloudstackpack']
            instances = workflow_dict['instances']
            environment = workflow_dict['environment']
            
            cs_credentials = get_credentials_for(environment = environment, credential_type = CredentialType.CLOUDSTACK)
            cs_provider = CloudStackProvider(credentials = cs_credentials)
            
            serviceofferingid = cloudstackpack.offering.serviceofferingid

            for instance in instances:
                host = instance.hostname
                
                host_csattr = HostAttr.objects.get(host=host)

                cs_provider.change_offering_and_reboot(vm_id = host_csattr.vm_id, serviceofferingid = serviceofferingid)

                host_ready = check_ssh(server=host.address, username=host_csattr.vm_user, password=host_csattr.vm_password, wait=5, interval=10)

                if not host_ready:
                    error = "Host %s is not ready..." % host
                    LOG.warn(error)
                    raise Exception, error
                    return False

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
        return True