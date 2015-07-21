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
            master_instances_detail = []
            slave_instances_detail = []
            for instance in database.databaseinfra.instances.all():
                if instance.is_arbiter:
                    continue
                if instance.databaseinfra.get_driver().check_instance_is_master(instance):
                    master_instances_detail.append({
                        'instance': instance,
                        'is_master': True,
                        'offering_changed': False,
                    })
                else:
                    slave_instances_detail.append({
                        'instance': instance,
                        'is_master': False,
                        'offering_changed': False,
                    })
            instances_detail = master_instances_detail + slave_instances_detail
            workflow_dict['instances_detail'] = instances_detail

            if len(instances_detail) == 1:
                context_dict = {'IS_HA': False}
            else:
                context_dict = {'IS_HA': True}

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
