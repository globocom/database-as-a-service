# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import get_credentials_for
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_cloudstack.models import HostAttr
from dbaas_credentials.models import CredentialType
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class RemoveVms(BaseStep):

    def __unicode__(self):
        return "Removing VMs..."

    def do(self, workflow_dict):
        try:

            cs_credentials = get_credentials_for(
                environment=workflow_dict['source_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            for source_host in workflow_dict['source_hosts']:
                host_attr = HostAttr.objects.get(host=source_host)
                LOG.info("Destroying virtualmachine %s" % host_attr.vm_id)

                cs_provider.destroy_virtual_machine(
                    project_id=cs_credentials.project,
                    environment=workflow_dict['source_environment'],
                    vm_id=host_attr.vm_id)

                host_attr.delete()
                LOG.info("HostAttr deleted!")

                source_host.delete()
                LOG.info("Source host deleted")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
