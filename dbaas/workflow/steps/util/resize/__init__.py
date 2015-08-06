
# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import check_ssh
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for

LOG = logging.getLogger(__name__)


def start_vm(workflow_dict):
    try:
        environment = workflow_dict['environment']
        cs_credentials = get_credentials_for(
            environment=environment, credential_type=CredentialType.CLOUDSTACK)
        cs_provider = CloudStackProvider(credentials=cs_credentials)

        host = workflow_dict['host']
        host_csattr = HostAttr.objects.get(host=host)
        started = cs_provider.start_virtual_machine(vm_id=host_csattr.vm_id)
        if not started:
            raise Exception("Could not start host {}".format(host))

        host_ready = check_ssh(server=host.address,
                               username=host_csattr.vm_user,
                               password=host_csattr.vm_password,
                               retries=50,
                               wait=20,
                               interval=30)

        if not host_ready:
            error = "Host %s is not ready..." % host
            LOG.warn(error)
            raise Exception(error)

        return True
    except Exception:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False


def stop_vm(workflow_dict):
    try:
        environment = workflow_dict['environment']
        cs_credentials = get_credentials_for(
            environment=environment, credential_type=CredentialType.CLOUDSTACK)
        cs_provider = CloudStackProvider(credentials=cs_credentials)
        host = workflow_dict['host']
        host_csattr = HostAttr.objects.get(host=host)
        stoped = cs_provider.stop_virtual_machine(vm_id=host_csattr.vm_id)
        if not stoped:
            raise Exception("Could not stop host {}".format(host))

        return True

    except Exception:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False
