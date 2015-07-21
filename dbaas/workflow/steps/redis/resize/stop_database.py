# -*- coding: utf-8 -*-
import logging
from . import run_vm_script
from ...util.base import BaseStep


LOG = logging.getLogger(__name__)


class StopDatabase(BaseStep):

    def __unicode__(self):
        return "Stoping Database..."

    def do(self, workflow_dict):
        context_dict = {
            'STOPDB': True,
        }

        ret_script = run_vm_script(
            workflow_dict=workflow_dict,
            context_dict=context_dict,
            script=workflow_dict['cloudstackpack'].script,
        )

        return ret_script

    def undo(self, workflow_dict):
        context_dict = {
            'STARTDB': True,
        }

        ret_script = run_vm_script(
            workflow_dict=workflow_dict,
            context_dict=context_dict,
            script=workflow_dict['original_cloudstackpack'].script,
        )

        return ret_script
