# -*- coding: utf-8 -*-
import logging
from workflow.steps.base import BaseStep
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from workflow.exceptions.error_codes import DBAAS_0015
from util import full_stack
from mongodb_share import start_vm, stop_vm


LOG = logging.getLogger(__name__)


class StopVM(BaseStep):
    def __unicode__(self):
        return "Stoping VMs..."
    
    def do(self, workflow_dict):
        return stop_vm(workflow_dict)
    
    def undo(self, workflow_dict):
        return start_vm(workflow_dict)