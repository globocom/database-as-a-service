# -*- coding: utf-8 -*-
import logging
from base import BaseStep
from dbaas_nfsaas.provider import NfsaasProvider


LOG = logging.getLogger(__name__)


class CreateNfs(BaseStep):

    def __unicode__(self):
        return "Creating DNS..."

    def do(self, workflow_dict):
        try:

            workflow_dict['disks'] = []

            for host in workflow_dict['hosts']:

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
            print e
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
            print e
            return False
