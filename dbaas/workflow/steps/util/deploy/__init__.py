# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command_host, check_ssh, full_stack, \
    build_context_script
from workflow.exceptions.error_codes import DBAAS_0015
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for

LOG = logging.getLogger(__name__)


def run_vm_script(workflow_dict, context_dict, script):
    try:
        instances_detail = workflow_dict['instances_detail']

        final_context_dict = dict(
            context_dict.items() + workflow_dict['initial_context_dict'].items())

        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            final_context_dict['HOSTADDRESS'] = instance.address
            final_context_dict['PORT'] = instance.port
            command = build_context_script(final_context_dict, script)
            output = {}
            return_code = exec_remote_command_host(host, command, output)
            if return_code:
                raise Exception, "Could not run script. Output: {}".format(
                    output)

        return True

    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False


def start_vm(workflow_dict):
    try:
        environment = workflow_dict['environment']
        cs_credentials = get_credentials_for(
            environment=environment, credential_type=CredentialType.CLOUDSTACK)
        cs_provider = CloudStackProvider(credentials=cs_credentials)
        instances_detail = workflow_dict['instances_detail']

        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_csattr = HostAttr.objects.get(host=host)
            started = cs_provider.start_virtual_machine(
                vm_id=host_csattr.vm_id)
            if not started:
                raise Exception, "Could not start host {}".format(host)

        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_ready = check_ssh(host, wait=5, interval=10)
            if not host_ready:
                error = "Host %s is not ready..." % host
                LOG.warn(error)
                raise Exception, error

        return True
    except Exception, e:
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
        instances_detail = workflow_dict['instances_detail']

        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_csattr = HostAttr.objects.get(host=host)
            stoped = cs_provider.stop_virtual_machine(vm_id=host_csattr.vm_id)
            if not stoped:
                raise Exception, "Could not stop host {}".format(host)

        return True

    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False
