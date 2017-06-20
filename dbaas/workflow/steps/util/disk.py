# -*- coding: utf-8 -*-
import logging
from util import exec_remote_command_host
from base import BaseInstanceStep
from nfsaas_utils import create_disk
from nfsaas_utils import delete_disk

LOG = logging.getLogger(__name__)


class Disk(BaseInstanceStep):
    OLD_DIRECTORY = '/data'
    NEW_DIRECTORY = '/new_data'

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
        self.newer_export = self.host.nfsaas_host_attributes.last()

    def do(self):
        script = 'mkdir -p {} && mount -t nfs -o bg,intr {} {}'.format(
            self.NEW_DIRECTORY, self.newer_export.nfsaas_path, self.NEW_DIRECTORY
        )

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not mount {} - {}: {}'.format(
                    self.NEW_DIRECTORY, return_code, output
                )
            )

    def undo(self):
        script = 'umount {}'.format(self.NEW_DIRECTORY)

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not umount {} - {}: {}'.format(
                    self.NEW_DIRECTORY, return_code, output
                )
            )


class CopyDataBetweenExports(Disk):

    def __unicode__(self):
        return "Coping data {} -> {}...".format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )

    def do(self):
        script = "rsync -ar --exclude='{}/.snapshot' {}/* {}".format(
            self.OLD_DIRECTORY, self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not copy data {} -> {} | {}: {}'.format(
                    self.OLD_DIRECTORY, self.NEW_DIRECTORY, return_code, output
                )
            )


class UnmountOldestExport(Disk):

    def __unicode__(self):
        return "Unmounting {}...".format(self.OLD_DIRECTORY)

    def do(self):
        script = 'umount {}'.format(self.OLD_DIRECTORY)

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not unmount {} -> {}: {}'.format(
                    self.OLD_DIRECTORY, return_code, output
                )
            )


class UnmountNewerExport(Disk):

    def __unicode__(self):
        return "Unmounting {}...".format(self.NEW_DIRECTORY)

    def do(self):
        script = 'umount {}'.format(self.NEW_DIRECTORY)

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not unmount {} -> {}: {}'.format(
                    self.NEW_DIRECTORY, return_code, output
                )
            )


class MountingNewerExport(MountNewerExport):

    def __unicode__(self):
        return "Mouting new disk {}...".format(self.NEW_DIRECTORY)

    def do(self):
        script = 'mount -t nfs -o bg,intr {} {}'.format(
            self.newer_export.nfsaas_path, self.OLD_DIRECTORY
        )

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not mount {} - {}: {}'.format(
                    self.OLD_DIRECTORY, return_code, output
                )
            )

    def undo(self):
        script = 'umount {}'.format(self.OLD_DIRECTORY)

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not umount {} - {}: {}'.format(
                    self.OLD_DIRECTORY, return_code, output
                )
            )


class DisableOldestExport(MountingNewerExport):

    def __unicode__(self):
        return "Disabling oldest export..."

    def do(self):
        for export in self.host.nfsaas_host_attributes.all():
            if export == self.newer_export:
                continue
            export.is_active = False
            export.save()

    def undo(self):
        for export in self.host.nfsaas_host_attributes.all():
            if len(export.snapshots) <= 0:
                continue

            export.is_active = True
            export.save()


class ConfigureFstab(MountingNewerExport):

    def __unicode__(self):
        return "Configuring fstab..."

    def do(self):
        script = 'sed \'{}/d\' "/etc/fstab"'.format(self.OLD_DIRECTORY)
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could remove {} from fstab - {}: {}'.format(
                    self.OLD_DIRECTORY, return_code, output
                )
            )

        script = 'echo "{} {} nfs defaults,bg,intr,nolock 0 0" >> /etc/fstab'.format(
            self.OLD_DIRECTORY, self.newer_export.nfsaas_path,
        )
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could configure {} in fstab - {}: {}'.format(
                    self.OLD_DIRECTORY, return_code, output
                )
            )


class FilePermissions(MountingNewerExport):

    def __unicode__(self):
        return "Changing filer permission..."

    def __init__(self, instance):
        super(FilePermissions, self).__init__(instance)
        self.user = self.databaseinfra.engine_name
        self.group = self.databaseinfra.engine_name

    def do(self):
        script = '''
            chown {1}:{2} {0} &&
            chmod g+r {0} &&
            chmod g+x {0}
        '''.format(self.OLD_DIRECTORY, self.user, self.group)
        output = {}

        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could set permissions - {}: {}'.format(return_code, output)
            )
