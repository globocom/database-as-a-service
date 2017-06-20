# -*- coding: utf-8 -*-
import logging
from base import BaseInstanceStep
from nfsaas_utils import create_disk
from nfsaas_utils import delete_disk

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


class MountNewerExport(Disk):

    def __unicode__(self):
        return "Mounting Export..."

    def __init__(self, instance):
        super(MountNewerExport, self).__init__(instance)
        newer_disk = self.hostname.disk

    def do(self):
        'mount -t nfs -o bg,intr {{EXPORT_PATH}} /data2'
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
