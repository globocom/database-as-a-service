# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command, check_ssh
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from util import build_context_script
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for

LOG = logging.getLogger(__name__)


def run_vm_script(workflow_dict, context_dict, script):
    try:
        instances_detail = workflow_dict['instances_detail']
        
        final_context_dict = dict(context_dict.items() + workflow_dict['initial_context_dict'].items())
        
        for instance_detail in instances_detail:
            host = instance_detail['instance'].hostname
            host_csattr = HostAttr.objects.get(host=host) 
            final_context_dict['IS_MASTER'] = instance_detail['is_master']
            command = build_context_script(final_context_dict, script)
            output = {} 
            return_code = exec_remote_command(server = host.address,
                                              username = host_csattr.vm_user,
                                              password = host_csattr.vm_password,
                                              command = command,
                                              output = output)
            if return_code:
                raise Exception, "Could not run script. Output: {}".format(output)

        return True
        
    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False


def start_vm(workflow_dict):
    try:
        environment = workflow_dict['environment']
        cs_credentials = get_credentials_for(environment = environment, credential_type = CredentialType.CLOUDSTACK)
        cs_provider = CloudStackProvider(credentials = cs_credentials)
        instances_detail = workflow_dict['instances_detail']
        
        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_csattr = HostAttr.objects.get(host=host)
            started = cs_provider.start_virtual_machine(vm_id = host_csattr.vm_id)
            if not started:
                raise Exception, "Could not start host {}".format(host)

        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_csattr = HostAttr.objects.get(host=host)
            host_ready = check_ssh(server=host.address, username=host_csattr.vm_user, password=host_csattr.vm_password, wait=5, interval=10)
            if not host_ready:
                error = "Host %s is not ready..." % host
                LOG.warn(error)
                raise Exception, error
        
        # wait database starting
        from time import sleep
        sleep(60)
        
        return True
    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False


def stop_vm(workflow_dict):
    try:
        environment = workflow_dict['environment']
        cs_credentials = get_credentials_for(environment = environment, credential_type = CredentialType.CLOUDSTACK)
        cs_provider = CloudStackProvider(credentials = cs_credentials)
        instances_detail = workflow_dict['instances_detail']
        
        for instance_detail in instances_detail:
            instance = instance_detail['instance']
            host = instance.hostname
            host_csattr = HostAttr.objects.get(host=host)
            stoped = cs_provider.stop_virtual_machine(vm_id = host_csattr.vm_id)
            if not stoped:
                raise Exception, "Could not stop host {}".format(host)

        return True

    except Exception, e:
        traceback = full_stack()

        workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
        workflow_dict['exceptions']['traceback'].append(traceback)

        return False