# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from dbaas_aclapi.tasks import replicate_acl_for

LOG = logging.getLogger(__name__)


class ReplicateOldAcl(BaseStep):
    def __unicode__(self):
        return "Replicating old acls ..."

    def do(self, workflow_dict):

        try:
            source_instances = workflow_dict['source_instances']
            source_secondary_ips = workflow_dict['source_secondary_ips']
            database = workflow_dict['database']

            for source_instance in source_instances:
                target_instance = source_instance.future_instance
                replicate_acl_for(database=database,
                                  old_ip=source_instance.address,
                                  new_ip=target_instance.address)

            for source_secondary_ip in source_secondary_ips:
                target_secondary_ip = source_secondary_ip.equivalent_dbinfraattr
                replicate_acl_for(database=database,
                                  old_ip=source_secondary_ip.ip,
                                  new_ip=target_secondary_ip.ip)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
