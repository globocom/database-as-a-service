# -*- coding: utf-8 -*-
import logging
from util import full_stack
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0019

LOG = logging.getLogger(__name__)


class AddInstancesReplicaSet(BaseStep):

    def __unicode__(self):
        return "Adding instances to replica set..."

    def do(self, workflow_dict):
        try:

            ## temporary code
            workflow_dict['source_instances'] = []
            for target_instance in workflow_dict['databaseinfra'].instances.filter(future_instance__isnull = False):
                workflow_dict['source_instances'].append(target_instance)
            LOG.info(workflow_dict['source_instances'])
            
            #for index, source_instance in enumerate(workflow_dict['source_instances']):
                
                
                
                

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
