# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import get_credentials_for
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.models import DatabaseInfraOffering
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0015

LOG = logging.getLogger(__name__)


class ResizeVM(BaseStep):

    def __unicode__(self):
        return "Resizing VMs..."

    def do(self, workflow_dict):
        try:

            cloudstackpack = workflow_dict['cloudstackpack']
            environment = workflow_dict['environment']

            cs_credentials = get_credentials_for(
                environment=environment, credential_type=CredentialType.CLOUDSTACK)
            cs_provider = CloudStackProvider(credentials=cs_credentials)

            serviceofferingid = cloudstackpack.offering.serviceofferingid

            host = workflow_dict['host']
            host_csattr = HostAttr.objects.get(host=host)
            offering_changed = cs_provider.change_service_for_vm(
                vm_id=host_csattr.vm_id, serviceofferingid=serviceofferingid)
            if not offering_changed:
                raise Exception("Could not change offering for Host {}".format(host))
            workflow_dict['offering_changed'] = True

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            original_cloudstackpack = workflow_dict['original_cloudstackpack']
            environment = workflow_dict['environment']

            cs_credentials = get_credentials_for(
                environment=environment, credential_type=CredentialType.CLOUDSTACK)
            cs_provider = CloudStackProvider(credentials=cs_credentials)

            original_serviceofferingid = original_cloudstackpack.offering.serviceofferingid

            if workflow_dict['offering_changed']:
                host = workflow_dict['host']
                host_csattr = HostAttr.objects.get(host=host)
                offering_changed = cs_provider.change_service_for_vm(
                    vm_id=host_csattr.vm_id, serviceofferingid=original_serviceofferingid)
                if not offering_changed:
                    raise Exception("Could not change offering for Host {}".format(host))
                else:
                    LOG.info('No resize to instance {}'.format(workflow_dict['instance']))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
