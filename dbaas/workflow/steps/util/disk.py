# -*- coding: utf-8 -*-
import logging
from util import exec_remote_command_host
from base import BaseInstanceStep

LOG = logging.getLogger(__name__)


class Disk(BaseInstanceStep):
    OLD_DIRECTORY = '/data'
    NEW_DIRECTORY = '/new_data'

    @property
    def is_valid(self):
        return bool(self.instance.hostname.volumes.first())

    @property
    def has_active(self):
        return self.host.volumes.filter(is_active=True).exists()


class DiskCommand(Disk):

    @property
    def scripts(self):
        raise NotImplementedError

    def do(self):
        if not self.is_valid:
            return

        for message, script in self.scripts.items():
            output = {}
            return_code = exec_remote_command_host(self.host, script, output)
            if return_code != 0:
                raise EnvironmentError(
                    '{} - {}: {}'.format(message, return_code, output)
                )

    def undo(self):
        # TODO
        pass


class CopyDataBetweenExports(DiskCommand):

    def __unicode__(self):
        return "Coping data {} -> {}...".format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )

    @property
    def scripts(self):
        message = 'Could not copy data {} -> {}'.format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY)
        script = "rsync -arm --exclude='{0}/.snapshot' {0}/* {1}".format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )
        return {message: script}


class CopyDataBetweenExportsMigration(CopyDataBetweenExports):
    NEW_DIRECTORY = '{}/data'.format(CopyDataBetweenExports.OLD_DIRECTORY)
    OLD_DIRECTORY = '{}/data'.format(CopyDataBetweenExports.NEW_DIRECTORY)

    @property
    def is_valid(self):
        is_valid = super(CopyDataBetweenExportsMigration, self).is_valid
        if not is_valid:
            return False

        if not self.infra.plan.has_persistence:
            return False

        return True

    @property
    def host(self):
        host = super(CopyDataBetweenExportsMigration, self).host
        return host.future_host


class CleanData(DiskCommand):
    def __unicode__(self):
        if not self.is_valid:
            return "Skipped because the instance is master"
        return "Removing data from slave..."

    @property
    def is_valid(self):
        return self.restore.is_slave(self.instance)

    @property
    def directory(self):
        return '{}/data/*'.format(self.OLD_DIRECTORY)

    @property
    def scripts(self):
        message = 'Could not remove data from {}'.format(self.OLD_DIRECTORY)
        script = 'rm -rf {}'.format(self.directory)
        return {message: script}


class CleanSSLDir(CleanData):

    @property
    def is_valid(self):
        return True

    @property
    def directory(self):
        return '/data/ssl/*'

    @property
    def scripts(self):
        message = 'Could not remove data from {}'.format(self.OLD_DIRECTORY)
        script = '[ -d /data/ssl ] && rm -rf {} || mkdir -p /data/ssl'.format(
            self.directory
        )
        return {message: script}


class CleanDataRecreateSlave(CleanData):
    @property
    def is_valid(self):
        return self.instance.is_slave

    def do(self):
        if self.is_database_instance:
            super(CleanDataRecreateSlave, self).do()


class CleanReplRecreateSlave(CleanData):
    @property
    def is_valid(self):
        return self.instance.is_slave

    @property
    def directory(self):
        return '{}/repl/*'.format(self.OLD_DIRECTORY)


class CleanDataArbiter(CleanData):

    def __unicode__(self):
        return "Removing data from arbiter..."

    @property
    def is_valid(self):
        return self.instance.instance_type == self.instance.MONGODB_ARBITER


class RemoveDeprecatedFiles(DiskCommand):

    def __unicode__(self):
        return "Removing deprecated files..."

    @property
    def scripts(self):
        driver = self.infra.get_driver()
        return {'Remove Deprecated': driver.remove_deprectaed_files()}


class ChangeSnapshotOwner(Disk):
    def __unicode__(self):
        return "Change snapshots owner..."

    @property
    def can_run(self):
        if self.host_migrate.database_migrate:
            return False
        return super(ChangeSnapshotOwner, self).can_run

    def do(self):
        for volume in self.instance.hostname.volumes.all():
            volume.is_active = False
            volume.host = self.host
            volume.save()

    def undo(self):
        volume = None
        for volume in self.host.volumes.filter(is_active=False):
            volume.host = self.instance.hostname
            volume.save()

        if volume:
            volume.is_active = True
            volume.save()
