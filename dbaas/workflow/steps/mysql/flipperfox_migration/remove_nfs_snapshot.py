# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class RemoveNfsSnapshot(BaseStep):

    def __unicode__(self):
        return "Removing nfs snapshot..."

    def do(self, workflow_dict):
        try:
            from dbaas_nfsaas.models import HostAttr
            databaseinfra = workflow_dict['databaseinfra']
            instance = workflow_dict['source_instances'][0]

            host_attr = HostAttr.objects.get(host=instance.hostname,
                                             is_active=True)

            NfsaasProvider.remove_snapshot(environment=databaseinfra.environment,
                                           host_attr=host_attr,
                                           snapshot_id=workflow_dict['snapshopt_id'])

            del workflow_dict['snapshopt_id']

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
