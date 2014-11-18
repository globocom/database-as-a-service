# -*- coding: utf-8 -*-
import logging
from workflow.steps.base import BaseStep
from dbaas_cloudstack.models import HostAttr
from util import exec_remote_command
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from mysql_share import run_vm_script


LOG = logging.getLogger(__name__)


class ChangeDatabaseConfigFile(BaseStep):
    def __unicode__(self):
        return "Changing database config file..."
    
    def do(self, workflow_dict):
        context_dict = {
            'CONFIGFILE': True,
        }
        
        ret_script = run_vm_script(
            workflow_dict = workflow_dict,
            context_dict = context_dict,
            script = workflow_dict['cloudstackpack'].script,
        )
        
        return ret_script
    
    def undo(self, workflow_dict):
        context_dict = {
            'CONFIGFILE': True,
            'STOPDB': True,
            'STARTDB': True,
        }
        
        ret_script = run_vm_script(
            workflow_dict = workflow_dict,
            context_dict = context_dict,
            script = workflow_dict['original_cloudstackpack'].script,
        )
        
        return ret_script
