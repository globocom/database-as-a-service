from datetime import datetime
from requests import post, delete, get
from backup.models import Snapshot
from dbaas_credentials.models import CredentialType
from util import get_credentials_for, exec_remote_command_host
from physical.models import Volume
from base import BaseInstanceStep


class VolumeProviderException(Exception):
    pass


class VolumeProviderRemoveSnapshotMigrate(VolumeProviderException):
    pass


class VolumeProviderBase(BaseInstanceStep):

    def __init__(self, instance):
        super(VolumeProviderBase, self).__init__(instance)
        self._credential = None

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.VOLUME_PROVIDER
            )
        return self._credential

    @property
    def volume(self):
        return self.host.volumes.get(is_active=True)

    @property
    def volume_migrate(self):
        return self.host_migrate.host.volumes.get(is_active=True)

    @property
    def provider(self):
        return self.credential.project

    @property
    def base_url(self):
        return "{}/{}/{}/".format(
            self.credential.endpoint, self.provider, self.environment
        )

    def create_volume(self, group, size_kb, to_address, snapshot_id=None, is_active=True):
        url = self.base_url + "volume/new"
        data = {
            "group": group,
            "size_kb": size_kb,
            "to_address": to_address,
            "snapshot_id": snapshot_id
        }

        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        volume = Volume()
        volume.host = self.host
        volume.identifier = response.json()['identifier']
        volume.total_size_kb = self.infra.disk_offering.size_kb
        volume.is_active = is_active
        volume.save()
        return volume

    def destroy_volume(self, volume):
        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)
        volume.delete()

    def get_volume(self, volume):
        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = get(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def get_path(self, volume):
        vol = self.get_volume(volume)
        return vol['path']

    def run_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not execute script {}: {}'.format(
                    return_code, output
                )
            )
        return output

    def take_snapshot(self):
        url = "{}snapshot/{}".format(self.base_url, self.volume.identifier)
        data = {
            "engine": self.engine.name,
            "db_name": self.database.name,
            "team_name": self.database.team.name
        }
        response = post(url, json=data)

        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def delete_snapshot(self, snapshot, force):
        url = "{}snapshot/{}?force={}".format(self.base_url, snapshot.snapshopt_id,
                                     force)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['removed']

    def restore_snapshot(self, snapshot):
        url = "{}snapshot/{}/restore".format(
            self.base_url, snapshot.snapshopt_id
        )
        response = post(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def add_access(self, volume, host):
        url = "{}access/{}".format(self.base_url, volume.identifier)
        data = {"to_address": host.address}
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def remove_access(self, volume, host):
        url = "{}access/{}/{}".format(
            self.base_url,
            volume.identifier,
            host.address
        )
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def get_mount_command(self, volume, data_directory="/data", fstab=True):
        url = "{}commands/{}/mount".format(self.base_url, volume.identifier)
        data = {
            'with_fstab': fstab,
            'data_directory': data_directory
        }
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['command']

    def get_copy_files_command(self, snapshot, source_dir, dest_dir):
        # snap = volume.backups.order_by('created_at').first()
        url = "{}commands/copy_files".format(self.base_url)
        data = {
            'snap_identifier': snapshot.snapshopt_id,
            'source_dir': source_dir,
            'dest_dir': dest_dir
        }
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['command']

    def get_umount_command(self, volume, data_directory="/data"):
        url = "{}commands/{}/umount".format(self.base_url, volume.identifier)
        data = {
            'data_directory': data_directory
        }
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['command']

    def clean_up(self, volume):
        url = "{}commands/{}/cleanup".format(self.base_url, volume.identifier)
        response = get(url)
        if not response.ok:
            raise IndexError(response.content, response)
        command = response.json()['command']
        if command:
            self.run_script(command)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class VolumeProviderBaseMigrate(VolumeProviderBase):

    @property
    def host(self):
        return self.host_migrate.host


class NewVolume(VolumeProviderBase):
    is_active = True

    def __unicode__(self):
        return "Creating Volume..."

    def do(self):
        if not self.instance.is_database:
            return
        snapshot = None
        if self.host_migrate and self.step_manager.snapshot:
            snapshot = self.step_manager.snapshot
        self.create_volume(
            self.infra.name,
            self.disk_offering.size_kb,
            self.host.address,
            snapshot_id=snapshot.snapshopt_id if snapshot else None,
            is_active=self.is_active
        )

    def undo(self):
        if not self.instance.is_database:
            return

        for volume in self.host.volumes.all():
            self.add_access(volume, self.host)
            self.clean_up(volume)
            self.destroy_volume(volume)


class NewInactiveVolume(NewVolume):
    def __unicode__(self):
        return "Creating Inactive Volume..."

    def do(self):
        self.is_active = False
        return super(NewInactiveVolume, self).do()


class MountDataVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Mounting {} volume...".format(self.directory)

    @property
    def directory(self):
        return "/data"

    @property
    def is_valid(self):
        return self.instance.is_database

    def do(self):
        if not self.is_valid:
            return

        script = self.get_mount_command(self.volume)
        self.run_script(script)

    def undo(self):
        pass


class MountDataNewVolume(MountDataVolume):
    @property
    def is_valid(self):
        return True

    @property
    def volume(self):
        return self.latest_disk


class MountDataLatestVolume(MountDataVolume):

    def __unicode__(self):
        return "Mounting new volume on {} for copy...".format(self.directory)

    @property
    def directory(self):
        return "/data_latest_volume"

    def do(self):
        script = self.get_mount_command(
            self.latest_disk,
            data_directory=self.directory,
            fstab=False
        )
        self.run_script(script)

    def undo(self):
        script = self.get_umount_command(
            self.latest_disk,
            data_directory=self.directory,
        )
        self.run_script(script)


class UnmountDataLatestVolume(MountDataLatestVolume):

    def __unicode__(self):
        return "Umounting new volume on {} for copy...".format(self.directory)

    def do(self):
        return super(UnmountDataLatestVolume, self).undo()

    def undo(self):
        return super(UnmountDataLatestVolume, self).do()


class MountDataVolumeMigrate(MountDataVolume):

    def __unicode__(self):
        return "Mounting old volume in new instance on dir {}...".format(self.directory)

    @property
    def directory(self):
        return "/data_migrate"

    @property
    def host_migrate_volume(self):
        return self.host_migrate.host.volumes.get(is_active=True)

    def do(self):
        script = self.get_mount_command(
            self.host_migrate_volume,
            data_directory=self.directory,
            fstab=False
        )
        self.run_script(script)

    def undo(self):
        script = self.get_umount_command(
            self.host_migrate_volume,
            data_directory=self.directory,
        )
        self.run_script(script)


class UmountDataVolumeMigrate(MountDataVolumeMigrate):

    def __unicode__(self):
        return "Dismounting old volume in new instance on dir {}...".format(self.directory)

    def do(self):
        return super(UmountDataVolumeMigrate, self).undo()

    def undo(self):
        return super(UmountDataVolumeMigrate, self).do()


class TakeSnapshotMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Doing backup for copy..."

    def do(self):
        from backup.tasks import make_instance_snapshot_backup
        from backup.models import BackupGroup
        group = BackupGroup()
        group.save()
        snapshot = make_instance_snapshot_backup(
            self.instance,
            {},
            group,
            provider_class=VolumeProviderBaseMigrate
        )

        if not snapshot:
            raise Exception('Backup was unsuccessful in {}'.format(self.instance))

        snapshot.is_automatic = False
        snapshot.save()
        self.step_manager.snapshot = snapshot
        self.step_manager.save()

        if snapshot.has_warning:
            raise Exception('Backup was warning')

    def undo(self):
        pass


class RemoveSnapshotMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Removing backup used on migrate..."

    def do(self):
        from backup.tasks import remove_snapshot_backup
        if not self.step_manager.snapshot:
            raise VolumeProviderRemoveSnapshotMigrate(
                'No snaoshot found on {} instance for migrate'.format(self.step_manager)
            )
        remove_snapshot_backup(self.step_manager.snapshot, self, force=1)

    def undo(self):
        pass


class CopyFilesMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Copying data to {} from {}...".format(
            self.source_directory,
            self.dest_directory
        )

    @property
    def source_directory(self):
        return "/data_migrate"

    @property
    def dest_directory(self):
        return "/data"

    def do(self):
        script = self.get_copy_files_command(
            self.step_manager.snapshot,
            self.source_directory,
            self.dest_directory
        )
        self.run_script(script)

    def undo(self):
        pass


class CopyFiles(VolumeProviderBase):

    def __unicode__(self):
        return "Copying data to {} from {}...".format(
            self.source_directory,
            self.dest_directory
        )

    @property
    def source_directory(self):
        return "/data"

    @property
    def dest_directory(self):
        return "/data_latest_volume"

    def do(self):
        script = "cp -rp {}/* {}".format(self.source_directory, self.dest_directory)
        self.run_script(script)

    def undo(self):
        pass


class CopyPermissions(VolumeProviderBase):

    def __unicode__(self):
        return "Copying permissions from {} to {}...".format(
            self.source_directory,
            self.dest_directory
        )

    @property
    def source_directory(self):
        return "/data"

    @property
    def dest_directory(self):
        return "/data_latest_volume"

    def do(self):
        script = ('stat -c "%a" {0} | xargs -I{{}} chmod {{}} {1}'
                  ' && stat -c "%U:%G" {0} | xargs -I{{}} chown {{}} {1}').format(
                    self.source_directory, self.dest_directory
        )
        self.run_script(script)

    def undo(self):
        pass


class MountDataVolumeRestored(MountDataVolume):

    @property
    def is_valid(self):
        if not super(MountDataVolumeRestored, self).is_valid:
            return False
        return self.restore.is_master(self.instance)

    @property
    def volume(self):
        return self.latest_disk


class UnmountActiveVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Umounting {} volume...".format(self.directory)

    @property
    def directory(self):
        return "/data"

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    def do(self):
        if not self.is_valid:
            return

        script = self.get_umount_command(self.volume)
        if script:
            self.run_script(script)

    def undo(self):
        pass


class UnmountDataVolume(UnmountActiveVolume):
    @property
    def is_valid(self):
        return True


class ResizeVolume(VolumeProviderBase):
    def __unicode__(self):
        return "Resizing data volume..."

    def do(self):
        if not self.instance.is_database:
            return

        url = "{}resize/{}".format(self.base_url, self.volume.identifier)
        data = {
            "new_size_kb": self.infra.disk_offering.size_kb,
        }

        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        volume = self.volume
        volume.total_size_kb = self.infra.disk_offering.size_kb
        volume.save()

    def undo(self):
        pass


class RestoreSnapshot(VolumeProviderBase):

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

        response = self.restore_snapshot(snapshot)
        volume = self.latest_disk
        volume.identifier = response['identifier']
        volume.is_active = False
        volume.id = None
        volume.host = self.disk_host
        volume.save()

    def undo(self):
        if not self.snapshot:
            return

        self.destroy_volume(self.latest_disk)


class AddAccess(VolumeProviderBase):

    @property
    def disk_time(self):
        raise NotImplementedError

    @property
    def volume(self):
        raise NotImplementedError

    def __unicode__(self):
        return "Adding permission to {} disk ...".format(self.disk_time)

    def do(self):
        if not self.is_valid:
            return
        self.add_access(self.volume, self.host)


class AddAccessRestoredVolume(AddAccess):

    @property
    def disk_time(self):
        return "restored"

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    @property
    def volume(self):
        return self.latest_disk


class AddAccessNewVolume(AddAccess):

    @property
    def disk_time(self):
        return "new"

    @property
    def is_valid(self):
        return True

    @property
    def volume(self):
        return self.latest_disk


class AddAccessMigrate(AddAccess):
    def __unicode__(self):
        return "Adding permission to old disk..."

    @property
    def volume(self):
        return self.host_migrate.host.volumes.get(is_active=True)

    def undo(self):
        self.remove_access(self.volume, self.host)


class RemoveAccessMigrate(AddAccessMigrate):
    def __unicode__(self):
        return "Removing permission to old disk..."

    def do(self):
        return super(RemoveAccessMigrate, self).undo()

    def undo(self):
        return super(RemoveAccessMigrate, self).do()


class TakeSnapshot(VolumeProviderBase):
    def __unicode__(self):
        return "Doing backup of old data..."

    @property
    def is_valid(self):
        return self.restore.is_master(self.instance)

    @property
    def group(self):
        return self.restore.new_group

    def do(self):
        if not self.is_valid:
            return

        snapshot = Snapshot.create(self.instance, self.group, self.volume)
        response = self.take_snapshot()
        snapshot.done(response)
        snapshot.status = Snapshot.SUCCESS
        snapshot.end_at = datetime.now()
        snapshot.save()

    def undo(self):
        pass


class TakeSnapshotOldDisk(TakeSnapshot):
        @property
        def is_valid(self):
            return True

        @property
        def group(self):
            from backup.models import BackupGroup
            group = BackupGroup()
            group.save()
            return group


class UpdateActiveDisk(VolumeProviderBase):

    def __unicode__(self):
        return "Updating meta data..."

    def do(self):
        if not self.instance.is_database:
            return

        old_disk = self.volume
        new_disk = self.latest_disk
        if old_disk != new_disk:
            old_disk.is_active = False
            new_disk.is_active = True
            old_disk.save()
            new_disk.save()

    def undo(self):
        pass


class DestroyOldEnvironment(VolumeProviderBase):

    def __unicode__(self):
        return "Removing old backups and volumes..."

    @property
    def environment(self):
        return self.infra.environment

    @property
    def host(self):
        return self.instance.hostname

    @property
    def can_run(self):
        if not self.instance.is_database:
            return False
        if not self.host_migrate.database_migrate:
            return False
        return super(DestroyOldEnvironment, self).can_run

    def do(self):
        from backup.tasks import remove_snapshot_backup
        for volume in self.host.volumes.all():
            for snapshot in volume.backups.all():
                remove_snapshot_backup(snapshot, self)
            self.add_access(volume, self.host)
            self.clean_up(volume)
            self.destroy_volume(volume)

    def undo(self):
        raise NotImplementedError
