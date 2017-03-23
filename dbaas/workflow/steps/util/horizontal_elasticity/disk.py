# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.base import BaseInstanceStep
from workflow.steps.util.nfsaas_utils import create_disk
from workflow.steps.util.nfsaas_utils import delete_disk

LOG = logging.getLogger(__name__)


class Disk(BaseInstanceStep):

    def __init__(self, instance):
        super(Disk, self).__init__(instance)

        self.databaseinfra = self.instance.databaseinfra
        self.environment = self.databaseinfra.environment
        self.host = self.instance.hostname

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateExport(Disk):

    def __unicode__(self):
        return "Creating Export..."

    def do(self):
        LOG.info('Creating export for {}'.format(self.instance))
        create_disk(
            environment=self.environment,
            host=self.host,
            size_kb=self.databaseinfra.disk_offering.size_kb
        )

    def undo(self):
        LOG.info('Running undo of CreateExport')
        delete_disk(
            environment=self.environment,
            host=self.host
        )
