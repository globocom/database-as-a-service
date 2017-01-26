# -*- coding: utf-8 -*-
import logging
from util import full_stack
from . import start_vm_func
from . import stop_vm_func
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0015

LOG = logging.getLogger(__name__)


class StopVM(BaseStep):

    def __unicode__(self):
        return "Stopping VM..."

    def do(self, workflow_dict):
        try:
            return stop_vm_func(workflow_dict)
        except Exception as e:
            LOG.error(e.message)
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)
            return False

    def undo(self, workflow_dict):
        try:
            return start_vm_func(workflow_dict)
        except Exception as e:
            LOG.error(e.message)
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)
            return False
