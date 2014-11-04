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
import re


LOG = logging.getLogger(__name__)


class StartDatabase(BaseStep):
    def __unicode__(self):
        return "Starting Database..."
    
    def do(self, workflow_dict):
        try:

            database = workflow_dict['database']
            cloudstackpack = workflow_dict['cloudstackpack']
            instances = workflow_dict['instances']
            regex = re.compile(r'[\r]')
                        
            for instance in instances:
                host = instance.hostname
                host_csattr = HostAttr.objects.get(host=host)
                output = {}
                command = regex.sub('', str(cloudstackpack.init_script))
                return_code = exec_remote_command(server = host.address,
                                                  username = host_csattr.vm_user,
                                                  password = host_csattr.vm_password,
                                                  command = command,
                                                  output = output)
                if return_code:
                    raise Exception, "Could not start database. Output: {}".format(output)
                    return False
                
            return True

        except Exception, e:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
    
    def undo(self, workflow_dict):
        return True