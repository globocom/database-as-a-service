# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from dbaas_aclapi.tasks import destroy_acl_for

LOG = logging.getLogger(__name__)


class RemoveOldAcl(BaseStep):
    def __unicode__(self):
        return "Deleting old acls..."

    def do(self, workflow_dict):
        try:
            source_instances = workflow_dict['source_instances']
            source_secondary_ips = workflow_dict['source_secondary_ips']
            database = workflow_dict['database']

            for source_instance in source_instances:
                destroy_acl_for(database=database, ip=source_instance.address)

            for source_secondary_ip in source_secondary_ips:
                destroy_acl_for(database=database, ip=source_secondary_ip.ip)

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
