# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.resize import start_vm
from workflow.steps.util.resize import stop_vm
from workflow.steps.util.base import BaseStep

LOG = logging.getLogger(__name__)


class StartVM(BaseStep):

    def __unicode__(self):
        return "Starting VMs..."

    def do(self, workflow_dict):
        try:
            return start_vm(workflow_dict)
        except Exception:
            return False

    def undo(self, workflow_dict):
        try:
            return stop_vm(workflow_dict)
        except Exception:
            return False
