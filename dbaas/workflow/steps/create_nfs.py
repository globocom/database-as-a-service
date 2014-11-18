# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from physical.models import Instance
from dbaas_nfsaas.provider import NfsaasProvider
from ..exceptions.error_codes import DBAAS_0009
from util import full_stack


LOG = logging.getLogger(__name__)


class CreateNfs(BaseStep):
    def __unicode__(self):
        return "Requesting NFS volume..."

    def do(self, workflow_dict):
        try:

            workflow_dict['disks'] = []

            for instance in workflow_dict['instances']:
                host = instance.hostname

                if instance.is_arbiter:
                    LOG.info("Do not creat nfsaas disk for Arbiter...")
                    continue

                LOG.info("Creating nfsaas disk...")

                disk = NfsaasProvider(
                ).create_disk(environment=workflow_dict['environment'],
                              plan=workflow_dict[
                                  'plan'],
                              host=host)

                if not disk:
                    return False

                workflow_dict['disks'].append(disk)

            return True

        except Exception, e:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            for host in workflow_dict['hosts']:
                LOG.info("Destroying nfsaas disk...")

                disk = NfsaasProvider().destroy_disk(
                    environment=workflow_dict['environment'], plan=workflow_dict['plan'], host=host)

                if not disk:
                    return False

            return True
        except Exception, e:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
