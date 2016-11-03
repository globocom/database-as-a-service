# -*- coding: utf-8 -*-
import logging
from util import full_stack
from physical.models import Instance
from workflow.steps.util.nfsaas_utils import create_disk, delete_disk
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0009

LOG = logging.getLogger(__name__)


class CreateNfs(BaseStep):

    def __unicode__(self):
        return "Requesting NFS volume..."

    def do(self, workflow_dict):
        try:
            workflow_dict['disks'] = []

            driver = workflow_dict['databaseinfra'].get_driver()
            non_database_instances = driver.get_non_database_instances()

            for instance in workflow_dict['instances']:
                if instance in non_database_instances:
                    LOG.info(
                        "Do not create NFS disk for '{}'...".format(instance)
                    )
                    continue

                plan = workflow_dict['plan']
                disk = create_disk(
                    environment=workflow_dict['environment'],
                    host=instance.hostname,
                    size_kb=plan.disk_offering.size_kb
                )
                if not disk:
                    return False

                workflow_dict['disks'].append(disk)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            for host in workflow_dict['hosts']:
                if not delete_disk(workflow_dict['environment'], host):
                    return False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
