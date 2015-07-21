# -*- coding: utf-8 -*-
import logging
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
            for instance in database.databaseinfra.instances.all():
                if instance.databaseinfra.get_driver().check_instance_is_master(instance):
                    is_master = True
                else:
                    is_master = False
                instances_detail.append({
                    'instance': instance,
                    'is_master': is_master,
                    'offering_changed': False,
                })

            workflow_dict['instances_detail'] = instances_detail

            if len(instances_detail) == 2:
                if instances_detail[0]['is_master']:
                    HOST01 = instances_detail[0]['instance'].hostname
                    HOST02 = instances_detail[1]['instance'].hostname
                else:
                    HOST01 = instances_detail[1]['instance'].hostname
                    HOST02 = instances_detail[0]['instance'].hostname
                context_dict = {
                    'MASTERPAIRNAME': database.databaseinfra.name,
                    'HOST01': HOST01,
                    'HOST02': HOST02,
                    'DBPASSWORD': database.databaseinfra.password,
                    'IS_HA': True
                }
            else:
                context_dict = {'IS_HA': False}

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
