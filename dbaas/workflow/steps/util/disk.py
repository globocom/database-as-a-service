# -*- coding: utf-8 -*-
import logging
from util import exec_remote_command_host
from base import BaseInstanceStep
from nfsaas_utils import create_disk, delete_disk, create_access

LOG = logging.getLogger(__name__)


class Disk(BaseInstanceStep):
    OLD_DIRECTORY = '/data'
    NEW_DIRECTORY = '/new_data'

    @property
    def environment(self):
        return self.databaseinfra.environment

    @property
    def host(self):
        return self.instance.hostname

    def __init__(self, instance):
        super(Disk, self).__init__(instance)
        self.databaseinfra = self.instance.databaseinfra


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


class NewerDisk(Disk):

    def __init__(self, instance):
        super(NewerDisk, self).__init__(instance)
        self.newer_export = self.host.nfsaas_host_attributes.last()


class DiskCommand(Disk):

    @property
    def scripts(self):
        raise NotImplementedError

    def do(self):
        for message, script in self.scripts.items():
            output = {}
            return_code = exec_remote_command_host(self.host, script, output)
            if return_code != 0:
                raise EnvironmentError(
                    '{} - {}: {}'.format(message, return_code, output)
                )


class DiskMountCommand(DiskCommand):

    def __unicode__(self):
        return "Mounting Export {}...".format(self.path_mount)

    @property
    def path_mount(self):
        raise NotImplementedError

    @property
    def export_remote_path(self):
        raise NotImplementedError

    @property
    def scripts(self):
        message = 'Could not mount {}'.format(self.path_mount)
        script = 'mkdir -p {0} && mount -t nfs -o bg,intr {1} {0}'.format(
            self.path_mount, self.export_remote_path
        )
        return {message: script}


class MountNewerExport(NewerDisk, DiskMountCommand):

    @property
    def path_mount(self):
        return self.NEW_DIRECTORY

    @property
    def export_remote_path(self):
        return self.newer_export.nfsaas_path


class CopyDataBetweenExports(DiskCommand):

    def __unicode__(self):
        return "Coping data {} -> {}...".format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )

    @property
    def scripts(self):
        message = 'Could not copy data {} -> {}'.format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY)
        script = "rsync -ar --exclude='{0}/.snapshot' {0}/* {1}".format(
            self.OLD_DIRECTORY, self.NEW_DIRECTORY
        )
        return {message: script}


class DiskUmountCommand(DiskCommand):

    def __unicode__(self):
        return "Unmounting {}...".format(self.mount_path)

    @property
    def mount_path(self):
        raise NotImplementedError

    @property
    def scripts(self):
        message = 'Could not unmount {}'.format(self.mount_path)
        script = 'umount {}'.format(self.mount_path)
        return {message: script}


class UnmountOldestExport(DiskUmountCommand):

    @property
    def mount_path(self):
        return self.OLD_DIRECTORY


class UnmountNewerExport(DiskUmountCommand):

    @property
    def mount_path(self):
        return self.NEW_DIRECTORY


class MountingNewerExport(MountNewerExport):

    @property
    def path_mount(self):
        return self.OLD_DIRECTORY


class DisableOldestExport(NewerDisk):

    def __unicode__(self):
        return "Disabling oldest export..."

    def do(self):
        for export in self.host.nfsaas_host_attributes.all():
            if export == self.newer_export:
                continue
            export.is_active = False
            export.save()


class ConfigureFstab(NewerDisk, DiskCommand):

    def __unicode__(self):
        return "Configuring fstab..."

    @property
    def scripts(self):
        remove_msg = 'Could remove {} from fstab'.format(self.OLD_DIRECTORY)
        remove_script = 'sed \'{}/d\' "/etc/fstab"'.format(self.OLD_DIRECTORY)

        add_msg = 'Could configure {} in fstab'.format(self.OLD_DIRECTORY)
        add_script = \
            'echo "{} {} nfs defaults,bg,intr,nolock 0 0" >> /etc/fstab'.format(
                self.OLD_DIRECTORY, self.newer_export.nfsaas_path,
            )

        return {
            remove_msg: remove_script,
            add_msg: add_script
        }


class FilePermissions(NewerDisk, DiskCommand):

    def __unicode__(self):
        return "Changing filer permission..."

    def __init__(self, instance):
        super(FilePermissions, self).__init__(instance)
        self.user = self.databaseinfra.engine_name
        self.group = self.databaseinfra.engine_name

    @property
    def scripts(self):
        script = '''
            chown {1}:{2} {0} &&
            chmod g+r {0} &&
            chmod g+x {0}
        '''.format(self.OLD_DIRECTORY, self.user, self.group)
        return {
            'Could set permissions': script
        }


class MigrationCreateExport(CreateExport):

    @property
    def environment(self):
        environment = super(MigrationCreateExport, self).environment
        return environment.migrate_environment

    @property
    def host(self):
        host = super(MigrationCreateExport, self).host
        return host.future_host


class AddDiskPermissionsOldest(Disk):

    def __unicode__(self):
        return "Adding oldest disk permission..."

    def get_disk_path(self):
        future_host = self.host.future_host
        disk = future_host.nfsaas_host_attributes.get(is_active=True)
        return disk.nfsaas_path_host

    def do(self):
        create_access(
            self.environment.migrate_environment,
            self.get_disk_path(), self.host.address
        )
