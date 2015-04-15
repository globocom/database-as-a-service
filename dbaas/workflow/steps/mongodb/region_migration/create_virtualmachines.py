# -*- coding: utf-8 -*-
import logging
from util import get_credentials_for
from util import full_stack
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.models import LastUsedBundle
from dbaas_cloudstack.models import DatabaseInfraOffering
from django.core.exceptions import ObjectDoesNotExist
from physical.models import Host
from physical.models import Instance
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0011

LOG = logging.getLogger(__name__)


class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Creating virtualmachines..."

    def do(self, workflow_dict):
        try:
            #LOG.debug(workflow_dict)
            
            cs_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            vm_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.VM)

            cs_provider = CloudStackProvider(credentials=cs_credentials)
            
            original_serviceoffering = workflow_dict['databaseinfra'].cs_dbinfra_offering.get().offering
            target_serviceoffering = original_serviceoffering.equivalent_offering
            
            #for source_host in workflow_dict['source_hosts']:
            #    source_host_name = source_host.hostname.split('.')[0]
            #
            #    vm = cs_provider.deploy_virtual_machine(
            #            offering=offering.target_serviceoffering.serviceofferingid,
            #            bundle= bundle,
            #            project_id=cs_credentials.project,
            #            vmname=vm_name,
            #            affinity_group_id=cs_credentials.get_parameter_by_name('affinity_group_id'),
            #    )

            if not vm:
                raise Exception("CloudStack could not create the virtualmachine")
            
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
