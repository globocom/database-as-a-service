# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class CreateNfs(BaseStep):

    def __unicode__(self):
        return "Requesting NFS volume..."

    def do(self, workflow_dict):
        try:

            workflow_dict['disks'] = []

            for instance in workflow_dict['target_instances']:

                if instance.instance_type == instance.MONGODB_ARBITER:
                    LOG.info("Do not creat nfsaas disk for Arbiter...")
                    continue

                if instance.instance_type == instance.REDIS_SENTINEL:
                    LOG.info("Do not creat nfsaas disk for Redis Sentinel...")
                    continue

                LOG.info("Creating nfsaas disk...")

                host = instance.hostname

                disk = NfsaasProvider().create_disk(
                    environment=workflow_dict['target_environment'],
                    plan=workflow_dict['target_plan'],
                    host=host)

                if not disk:
                    LOG.info("nfsaas disk could not be created...")
                    return False

                workflow_dict['disks'].append(disk)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            for host in workflow_dict['target_hosts']:
                LOG.info("Destroying nfsaas disk...")

                NfsaasProvider().destroy_disk(
                    environment=workflow_dict['target_environment'],
                    host=host)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
