# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict
from dbaas_nfsaas.models import HostAttr
from util import exec_remote_command_host
from base import BaseInstanceStep, BaseInstanceStepMigration
from nfsaas_utils import create_disk, delete_disk, create_access, \
    restore_snapshot, restore_wait_for_finished, delete_export
from restore_snapshot import make_host_backup

LOG = logging.getLogger(__name__)


class Disk(BaseInstanceStep):
    OLD_DIRECTORY = '/data'
    NEW_DIRECTORY = '/new_data'

    @property
    def is_valid(self):
        return bool(self.instance.hostname.nfsaas_host_attributes.first())

    @property
    def has_active(self):
        disks = self.host.nfsaas_host_attributes.filter(is_active=True)
        return len(disks) > 0


class CreateExport(Disk):

    def __unicode__(self):
        return "Creating Export..."

    @property
    def can_run(self):
        from util import get_credentials_for
        from dbaas_credentials.models import CredentialType
        try:
            credential = get_credentials_for(self.environment, CredentialType.FAAS)
        except IndexError:
            return False
        else:
            return True

    def do(self):
        if not self.host.database_instance():
            return

        if self.has_active:
            return

        LOG.info('Creating export for {}'.format(self.instance))
        create_disk(
            environment=self.environment,
            host=self.host,
            size_kb=self.infra.disk_offering.size_kb
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

    @property
    def newer_export(self):
        return self.host.nfsaas_host_attributes.last()


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
        script = 'mkdir -p {0} && mount -t nfs -o bg,intr,nolock {1} {0}'.format(
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
        script = "rsync -arm --exclude='{0}/.snapshot' {0}/* {1}".format(
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


class UnmountNewerExportMigration(
    UnmountNewerExport, BaseInstanceStepMigration
):
    pass


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

    def add_clone_script(self, scripts):
        error = 'Could not copy fstab'.format(self.OLD_DIRECTORY)
        script = 'cp /etc/fstab /etc/fstab.bkp'.format(self.OLD_DIRECTORY)
        scripts[error] = script

    def add_remove_script(self, scripts):
        error = 'Could not remove {} from fstab'.format(self.OLD_DIRECTORY)
        script = 'sed \'/\{}/d\' /etc/fstab.bkp > /etc/fstab'.format(
            self.OLD_DIRECTORY
        )
        scripts[error] = script

    def add_configure_script(self, scripts):
        error = 'Could not configure {} in fstab'.format(self.OLD_DIRECTORY)
        script = 'echo "{}   {} nfs defaults,bg,intr,nolock 0 0" >> /etc/fstab'.format(
            self.newer_export.nfsaas_path, self.OLD_DIRECTORY
        )
        scripts[error] = script

    @property
    def scripts(self):
        scripts = OrderedDict()
        self.add_clone_script(scripts)
        self.add_remove_script(scripts)
        self.add_configure_script(scripts)
        return scripts


class FilePermissions(NewerDisk, DiskCommand):

    def __unicode__(self):
        return "Changing filer permission..."

    def __init__(self, instance):
        super(FilePermissions, self).__init__(instance)
        self.user = self.infra.engine_name
        self.group = self.infra.engine_name

    def get_extra_folders_permissions(self):
        if self.user == "mysql":
            return '''mkdir {0}/repl &&
                cp -r {1}/repl {0}/repl &&
                chown mysql:mysql {0}/repl &&
                chmod g+r {0}/repl &&
                chmod g+x {0}/repl &&

                mkdir {0}/logs &&
                cp -r {1}/logs {0}/logs &&
                chown mysql:mysql {0}/logs &&
                chmod g+r {0}/logs &&
                chmod g+x {0}/logs &&

                mkdir {0}/tmp &&
                cp -r {1}/tmp {0}/tmp &&
                chown mysql:mysql {0}/tmp &&
                chmod g+r {0}/tmp &&
                chmod g+x {0}/tmp'''.format(
                self.OLD_DIRECTORY, self.NEW_DIRECTORY
            )

    @property
    def scripts(self):
        script = '''
            chown {1}:{2} {0} &&
            chown {1}:{2} {0}/data/ &&
            chmod g+r {0} &&
            chmod g+x {0} '''.format(self.OLD_DIRECTORY, self.user, self.group)

        extra = self.get_extra_folders_permissions()
        if extra:
            script = '''{} && {}'''.format(script, extra)

        return {
            'Could set permissions': script
        }


class FilePermissionsMigration(FilePermissions, BaseInstanceStepMigration):
    pass


class MigrationCreateExport(CreateExport, BaseInstanceStepMigration):
    pass

class AddDiskPermissions(Disk):

    @property
    def disk_time(self):
        raise NotImplementedError

    def disk_path(self):
        raise NotImplementedError

    @property
    def to_host(self):
        return self.host

    def __unicode__(self):
        return "Adding permission to {} disk ...".format(self.disk_time)

    def do(self):
        if not self.is_valid:
            return

        create_access(
            self.environment, self.disk_path(), self.to_host
        )

class AddDiskPermissionsOldest(AddDiskPermissions):

    @property
    def disk_time(self):
        return "Oldest"

    def disk_path(self):
        disk = self.host.nfsaas_host_attributes.get(is_active=True)
        return disk.nfsaas_path_host

    @property
    def to_host(self):
        return self.host.future_host


class MountOldestExportMigration(DiskMountCommand, BaseInstanceStepMigration):

    @property
    def path_mount(self):
        return self.NEW_DIRECTORY

    @property
    def export_remote_path(self):
        base_host = BaseInstanceStep(self.instance).host
        return base_host.nfsaas_host_attributes.get(is_active=True).nfsaas_path


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


class DisableOldestExportMigration(DisableOldestExport):

    def do(self):
        for export in self.host.future_host.nfsaas_host_attributes.all():
            export.is_active = False
            export.save()


class DiskUpdateHost(Disk):

    def __unicode__(self):
        return "Moving oldest disks to new host..."

    def do(self):
        for export in self.host.future_host.nfsaas_host_attributes.all():
            export.host = self.host
            export.save()


class RestoreSnapshot(Disk):

    def __unicode__(self):
        if not self.snapshot:
            return "Skipping restoring (No snapshot for this instance)..."

        return "Restoring {}...".format(self.snapshot)

    @property
    def disk_host(self):
        return self.restore.master_for(self.instance).hostname

    def do(self):
        snapshot = self.snapshot
        if not snapshot:
            return

        disk = HostAttr.objects.get(nfsaas_path=snapshot.export_path)
        restore_job = restore_snapshot(
            self.environment, disk.nfsaas_export_id, snapshot.snapshopt_id
        )
        job_result = restore_wait_for_finished(
            self.environment, restore_job['job']
        )

        if 'id' not in job_result:
            raise EnvironmentError(
                'Error while restoring snapshot - {}'.format(job_result)
            )

        disk = self.latest_disk
        disk.nfsaas_export_id = job_result['id']
        disk.nfsaas_path_host = job_result['path']
        disk.nfsaas_path = job_result['full_path']
        disk.is_active = False
        disk.id = None
        disk.host = self.disk_host
        disk.save()

    def undo(self):
        if not self.restore.is_master(self.instance):
            return

        delete_export(self.environment, self.latest_disk)


class AddDiskPermissionsRestoredDisk(AddDiskPermissions):

    @property
    def disk_time(self):
        return "restored"

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def disk_path(self):
        return self.latest_disk.nfsaas_path_host


class UnmountOldestExportRestore(UnmountOldestExport):

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def undo(self):
        # ToDo
        pass


class MountNewerExportRestore(MountNewerExport):

    @property
    def path_mount(self):
        return self.OLD_DIRECTORY

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def undo(self):
        # ToDo
        pass


class ConfigureFstabRestore(MountNewerExportRestore, ConfigureFstab):

    def undo(self):
        # ToDo
        pass


class CleanData(DiskCommand):

    def __unicode__(self):
        return "Removing data from slaves..."

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


class CleanDataArbiter(CleanData):

    def __unicode__(self):
        return "Removing data from arbiter..."

    @property
    def is_valid(self):
        return self.instance.instance_type == self.instance.MONGODB_ARBITER


class BackupRestore(Disk):

    def __unicode__(self):
        return "Doing backup of old data..."

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    @property
    def disk(self):
        return self.host.active_disk.nfsaas_export_id

    @property
    def group(self):
        return self.restore.new_group

    def do(self):
        if not self.is_valid:
            return

        if not make_host_backup(self.database, self.instance, self.disk, self.group):
            raise EnvironmentError(
                "Could not do backup of current database data in {}".format(
                    self.instance
                )
            )

    def undo(self):
        # ToDo
        pass


class UpdateRestore(Disk):

    def __unicode__(self):
        return "Updating meta data..."

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def do(self):
        if not self.is_valid:
            return

        old_disk = self.host.active_disk
        new_disk = self.host.nfsaas_host_attributes.last()

        if old_disk != new_disk:
            old_disk.is_active = False
            new_disk.is_active = True
            old_disk.save()
            new_disk.save()

    def undo(self):
        # ToDo
        pass


class RemoveDeprecatedFiles(DiskCommand):

    def __unicode__(self):
        return "Removing deprecated files..."

    @property
    def scripts(self):
        driver = self.infra.get_driver()
        return {'Remove Deprecated': driver.remove_deprectaed_files()}
