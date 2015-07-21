# -*- coding: utf-8 -*-
import logging
from physical.models import Instance
from util import full_stack
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0015

LOG = logging.getLogger(__name__)


class InitVariables(BaseStep):

    def __unicode__(self):
        return "Init variables..."

    def do(self, workflow_dict):
        try:

            database = workflow_dict['database']
            instances_detail = []
            for instance in database.databaseinfra.instances.filter(instance_type=Instance.REDIS):
                instances_detail.append({
                    'instance': instance,
                    #'is_master': is_master,
                    'offering_changed': False,
                })

            workflow_dict['instances_detail'] = instances_detail

            context_dict = {
                'IS_HA': False,
                'DBPASSWORD': database.databaseinfra.password,
                'DATABASENAME': database.name,
            }

            workflow_dict['initial_context_dict'] = context_dict
            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0015)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Nothing to do here...")
        return None
