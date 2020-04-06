from datetime import datetime
from time import sleep

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


class VolumeProviderRemoveVolumeMigrate(VolumeProviderException):
    pass


class VolumeProviderGetSnapshotState(VolumeProviderException):
    pass


class VolumeProviderScpFromSnapshotCommand(VolumeProviderException):
    pass


class VolumeProviderAddHostAllowCommand(VolumeProviderException):
    pass


class VolumeProviderCreatePubKeyCommand(VolumeProviderException):
    pass


class VolumeProviderRemovePubKeyCommand(VolumeProviderException):
    pass


class VolumeProviderRemoveHostAllowCommand(VolumeProviderException):
    pass


class VolumeProviderSnapshotHasWarningStatusError(VolumeProviderException):
    pass


class VolumeProviderSnapshotNotFoundError(VolumeProviderException):
    pass


class VolumeProviderBase(BaseInstanceStep):

    def __init__(self, instance):
        super(VolumeProviderBase, self).__init__(instance)
        self._credential = None

    @property
    def driver(self):
        return self.infra.get_driver()

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

    def create_volume(self, group, size_kb, to_address, snapshot_id=None,
                      is_active=True):
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

    def run_script(self, script, host=None):
        output = {}
        return_code = exec_remote_command_host(
            host or self.host,
            script,
            output
        )
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
        url = "{}snapshot/{}?force={}".format(
            self.base_url,
            snapshot.snapshopt_id,
            force
        )
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

    def add_access(self, volume, host, access_type=None):
        url = "{}access/{}".format(self.base_url, volume.identifier)
        data = {
            "to_address": host.address
        }
        if access_type:
            data['access_type'] = access_type
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def get_snapshot_state(self, snapshot):
        url = "{}snapshot/{}/state".format(
            self.base_url, snapshot.snapshopt_id
        )
        response = get(url)
        if not response.ok:
            raise VolumeProviderGetSnapshotState(response.content, response)
        return response.json()['state']

    def _get_command(self, url, payload, exception_class):
        response = get(url, json=payload)
        if not response.ok:
            raise exception_class(response.content, response)
        return response.json()['command']

    def get_create_pub_key_command(self, host_ip):
        url = "{}commands/create_pub_key".format(self.base_url)
        return self._get_command(
            url,
            {'host_ip': host_ip},
            VolumeProviderCreatePubKeyCommand
        )

    def get_remove_pub_key_command(self, host_ip):
        url = "{}commands/remove_pub_key".format(self.base_url)
        return self._get_command(
            url,
            {'host_ip': host_ip},
            VolumeProviderRemovePubKeyCommand
        )

    def get_add_hosts_allow_command(self, host_ip):
        url = "{}commands/add_hosts_allow".format(self.base_url)
        return self._get_command(
            url,
            {'host_ip': host_ip},
            VolumeProviderAddHostAllowCommand
        )

    def get_remove_hosts_allow_command(self, host_ip):
        url = "{}commands/remove_hosts_allow".format(self.base_url)
        return self._get_command(
            url,
            {'host_ip': host_ip},
            VolumeProviderRemoveHostAllowCommand
        )

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

    def get_copy_files_command(self, snapshot, source_dir, dest_dir,
                               snap_dir=''):
        # snap = volume.backups.order_by('created_at').first()
        url = "{}commands/copy_files".format(self.base_url)
        data = {
            'snap_identifier': snapshot.snapshopt_id,
            'source_dir': source_dir,
            'dest_dir': dest_dir,
            'snap_dir': snap_dir
        }
        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['command']

    def get_scp_from_snapshot_command(self, snapshot, source_dir, dest_ip,
                                      dest_dir):
        url = "{}snapshots/{}/commands/scp".format(
            self.base_url,
            snapshot.snapshopt_id
        )
        data = {
            'source_dir': source_dir,
            'target_ip': dest_ip,
            'target_dir': dest_dir
        }
        response = get(url, json=data)
        if not response.ok:
            raise VolumeProviderScpFromSnapshotCommand(
                response.content,
                response
            )
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

    @property
    def environment(self):
        return self.infra.environment


class NewVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Creating Volume..."

    @property
    def active_volume(self):
        return True

    @property
    def has_snapshot_on_step_manager(self):
        return (self.host_migrate and hasattr(self, 'step_manager')
                and self.host_migrate == self.step_manager)

    def _remove_volume(self, volume, host):
        self.destroy_volume(volume)

    def do(self):
        if not self.instance.is_database:
            return
        snapshot = None
        if self.has_snapshot_on_step_manager:
            snapshot = self.step_manager.snapshot
        elif self.host_migrate:
            snapshot = self.host_migrate.snapshot
        self.create_volume(
            self.infra.name,
            self.disk_offering.size_kb,
            self.host.address,
            snapshot_id=snapshot.snapshopt_id if snapshot else None,
            is_active=self.active_volume
        )

    def undo(self):
        if not self.instance.is_database or not self.host:
            return

        for volume in self.host.volumes.all():
            self._remove_volume(volume, self.host)


class NewVolumeMigrate(NewVolume):
    def __unicode__(self):
        return "Creating second volume based on snapshot for migrate..."

    @property
    def active_volume(self):
        return False

    @property
    def environment(self):
        return self.infra.environment

    @property
    def host(self):
        return self.host_migrate.host

    def undo(self):
        raise Exception("This step doesnt have roolback")


class NewVolumeOnSlaveMigrate(NewVolumeMigrate):
    @property
    def host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname


class NewVolumeOnSlaveMigrateFirstNode(VolumeProviderBase):
    """This class creates a new volume. This Step is only going to be executed
    during the first iteration."""

    def __init__(self, instance):
        super(NewVolumeOnSlaveMigrateFirstNode, self).__init__(instance)
        self.new_volume_step = NewVolumeOnSlaveMigrate(instance)

    def __unicode__(self):
        return str(self.new_volume_step)

    def is_first(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if self.is_first():
            self.new_volume_step.do()

    def undo(self):
        if self.is_first():
            self.new_volume_step.undo()


class RemoveVolumeMigrate(NewVolumeMigrate):
    def __unicode__(self):
        return "Removing second volume based on snapshot for migrate..."

    @property
    def host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname

    def do(self):
        vol = self.host.volumes.filter(is_active=False).last()
        if not vol:
            raise VolumeProviderRemoveVolumeMigrate(
                "Any inactive volume found"
            )
        self._remove_volume(vol, self.host)


class RemoveVolumeMigrateLastNode(VolumeProviderBase):
    """This class removes the last inactive volume. This Step is only going to
    be executed during the last iteration."""

    def __init__(self, instance):
        super(RemoveVolumeMigrateLastNode, self).__init__(instance)
        self.remove_volume_step = RemoveVolumeMigrate(instance)

    def __unicode__(self):
        return str(self.remove_volume_step)

    def is_last(self):
        return self.instance == self.infra.instances.last()

    def do(self):
        if self.is_last():
            self.remove_volume_step.do()

    def undo(self):
        if self.is_last():
            self.remove_volume_step.undo()


class NewInactiveVolume(NewVolume):
    def __unicode__(self):
        return "Creating Inactive Volume..."

    @property
    def active_volume(self):
        return False


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
        return "Mounting old volume in new instance on dir {}...".format(
            self.directory
        )

    @property
    def directory(self):
        return "/data_migrate"

    @property
    def host_migrate_volume(self):
        return self.host_migrate.host.volumes.get(is_active=True)

    @property
    def environment(self):
        return self.infra.environment

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


class MountDataVolumeRecreateSlave(MountDataVolumeMigrate):

    def __unicode__(self):
        return "Mounting master volume in slave instance on dir {}...".format(
            self.directory
        )

    @property
    def directory(self):
        return "/data_recreate_slave"

    @property
    def host_migrate_volume(self):
        master_instance = self.infra.get_driver().get_master_instance()
        return master_instance.hostname.volumes.get(is_active=True)

    def do(self):
        if self.is_database_instance:
            super(MountDataVolumeRecreateSlave, self).do()


class UmountDataVolumeRecreateSlave(MountDataVolumeRecreateSlave):

    def __unicode__(self):
        return "Umounting master volume in slave instance on dir {}...".format(
            self.directory
        )

    def do(self):
        if self.is_database_instance:
            super(UmountDataVolumeRecreateSlave, self).undo()

    def undo(self):
        if self.is_database_instance:
            super(UmountDataVolumeRecreateSlave, self).do()


class MountDataVolumeDatabaseMigrate(MountDataVolumeMigrate):
    def __unicode__(self):
        return "Mounting new volume for scp...".format(self.directory)

    @property
    def host(self):
        return self.host_migrate.host

    @property
    def host_migrate_volume(self):
        return self.host.volumes.filter(is_active=False).last()


class MountDataVolumeOnSlaveMigrate(MountDataVolumeDatabaseMigrate):
    @property
    def host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname


class MountDataVolumeOnSlaveFirstNode(VolumeProviderBase):
    """This class executes volume mounting on the slave instance. This Step is
    only going to be executed during the first iteration."""

    def __init__(self, instance):
        super(MountDataVolumeOnSlaveFirstNode, self).__init__(instance)
        self.mount_step = MountDataVolumeOnSlaveMigrate(instance)

    def __unicode__(self):
        return str(self.mount_step)

    def is_first(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if self.is_first():
            self.mount_step.do()

    def undo(self):
        if self.is_first():
            self.mount_step.undo()


class UmountDataVolumeDatabaseMigrate(MountDataVolumeDatabaseMigrate):
    def __unicode__(self):
        return "Umounting new volume for scp...".format(self.directory)

    def do(self):
        return super(UmountDataVolumeDatabaseMigrate, self).undo()

    def undo(self):
        return super(UmountDataVolumeDatabaseMigrate, self).do()


class UmountDataVolumeOnSlaveMigrate(UmountDataVolumeDatabaseMigrate):
    @property
    def host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname


class UmountDataVolumeOnSlaveLastNode(VolumeProviderBase):
    """This class executes volume unmounting on the slave instance. This Step
    is only going to be executed during the last iteration."""

    def __init__(self, instance):
        super(UmountDataVolumeOnSlaveLastNode, self).__init__(instance)
        self.umount_step = UmountDataVolumeOnSlaveMigrate(instance)

    def __unicode__(self):
        return str(self.umount_step)

    def is_last(self):
        return self.instance == self.infra.instances.last()

    def do(self):
        if self.is_last():
            self.umount_step.do()

    def undo(self):
        if self.is_last():
            self.umount_step.undo()


class UmountDataVolumeMigrate(MountDataVolumeMigrate):

    def __unicode__(self):
        return "Dismounting old volume in new instance on dir {}...".format(
            self.directory
        )

    def do(self):
        return super(UmountDataVolumeMigrate, self).undo()

    def undo(self):
        return super(UmountDataVolumeMigrate, self).do()


class TakeSnapshotMigrate(VolumeProviderBase):

    def __init__(self, *args, **kw):
        super(TakeSnapshotMigrate, self).__init__(*args, **kw)
        self._database_migrate = None

    def __unicode__(self):
        return "Doing backup for copy..."

    @property
    def is_database_migrate(self):
        return self.host_migrate and self.host_migrate.database_migrate

    @property
    def database_migrate(self):
        if self._database_migrate:
            return self._database_migrate
        self._database_migrate = (self.host_migrate and
                                  self.host_migrate.database_migrate)
        return self._database_migrate

    @property
    def provider_class(self):
        return VolumeProviderBaseMigrate

    @property
    def target_volume(self):
        return None

    def do(self):
        from backup.tasks import make_instance_snapshot_backup
        from backup.models import BackupGroup
        if (self.database_migrate
                and self.database_migrate.host_migrate_snapshot):
            snapshot = self.database_migrate.host_migrate_snapshot
        else:
            group = BackupGroup()
            group.save()
            snapshot = make_instance_snapshot_backup(
                self.instance,
                {},
                group,
                provider_class=self.provider_class,
                target_volume=self.target_volume
            )

            if not snapshot:
                raise VolumeProviderSnapshotNotFoundError(
                    'Backup was unsuccessful in {}'.format(
                        self.instance)
                )

            snapshot.is_automatic = False
            snapshot.save()
        if self.database_migrate:
            host_migrate = self.host_migrate
            host_migrate.snapshot = snapshot
            host_migrate.save()
        else:
            self.step_manager.snapshot = snapshot
            self.step_manager.save()

        if snapshot.has_warning:
            raise VolumeProviderSnapshotHasWarningStatusError(
                'Backup was warning'
            )

    def undo(self):
        pass


class TakeSnapshotFromMaster(TakeSnapshotMigrate):
    def __unicode__(self):
        return "Doing backup from master..."

    @property
    def provider_class(self):
        return TakeSnapshotFromMaster

    @property
    def target_volume(self):
        return self.volume

    @property
    def host(self):
        return self.instance.hostname

    @property
    def group(self):
        from backup.models import BackupGroup
        group = BackupGroup()
        group.save()
        return group

    def do(self):
        if self.is_database_instance:
            driver = self.infra.get_driver()
            self.instance = driver.get_master_instance()
            super(TakeSnapshotFromMaster, self).do()


class RemoveSnapshotMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Removing backup used on migrate..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        from backup.tasks import remove_snapshot_backup
        if self.is_database_instance:
            if self.host_migrate and self.host_migrate.database_migrate:
                snapshot = self.host_migrate.snapshot
            else:
                snapshot = self.step_manager.snapshot
            if not snapshot:
                raise VolumeProviderRemoveSnapshotMigrate(
                    'No snapshot found on {} instance for migration'.format(
                        self.step_manager
                    )
                )
            remove_snapshot_backup(snapshot, self, force=1)

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

    @property
    def snap_dir(self):
        return ""

    def do(self):
        script = self.get_copy_files_command(
            self.step_manager.snapshot,
            self.source_directory,
            self.dest_directory,
            self.snap_dir
        )
        self.run_script(script)

    def undo(self):
        pass


class CopyDataFromSnapShot(CopyFilesMigrate):

    def __unicode__(self):
        return "Copying data to snapshot to {}...".format(
            self.dest_directory
        )

    @property
    def source_directory(self):
        return "/data_recreate_slave"

    @property
    def dest_directory(self):
        return "/data/data"

    @property
    def snap_dir(self):
        return "data/"

    def do(self):
        if self.is_database_instance:
            super(CopyDataFromSnapShot, self).do()


class CopyReplFromSnapShot(CopyDataFromSnapShot):

    def __unicode__(self):
        return "Copying repl to snapshot to {}...".format(
            self.dest_directory
        )

    @property
    def dest_directory(self):
        return "/data/repl"

    @property
    def snap_dir(self):
        return "repl/"


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
        script = "cp -rp {}/* {}".format(
            self.source_directory,
            self.dest_directory
        )
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
                  ' && stat -c "%U:%G" {0} '
                  '| xargs -I{{}} chown {{}} {1}').format(
                    self.source_directory, self.dest_directory)
        self.run_script(script)


class ScpFromSnapshotMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Copying data from snapshot to new host..."

    @property
    def source_dir(self):
        return "/data"

    @property
    def dest_dir(self):
        return "/data"

    @property
    def environment(self):
        return self.infra.environment

    @property
    def host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname

    def do(self):
        if self.host_migrate and self.host_migrate.database_migrate:
            snapshot = self.host_migrate.snapshot
        else:
            snapshot = self.step_manager.snapshot

        script = self.get_scp_from_snapshot_command(
            snapshot,
            self.source_dir,
            self.host_migrate.host.future_host.address,
            self.dest_dir
        )
        self.run_script(script)

    def undo(self):
        pass


class ScpFromSnapshotDatabaseMigrate(ScpFromSnapshotMigrate):

    @property
    def source_dir(self):
        return "/data_migrate"


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

    @property
    def environment(self):
        return self.infra.environment

    def undo(self):
        self.remove_access(self.volume, self.host)


class AddAccessRecreateSlave(AddAccess):
    def __unicode__(self):
        return "Adding permission to old disk..."

    @property
    def volume(self):
        master_instance = self.infra.get_driver().get_master_instance()
        return master_instance.hostname.volumes.get(is_active=True)

    def do(self):
        if not self.is_valid and not self.is_database_instance:
            return
        self.add_access(self.volume, self.host, 'read-only')

    def undo(self):
        if self.is_database_instance:
            self.remove_access(self.volume, self.host)


class RemoveAccessRecreateSlave(AddAccessRecreateSlave):
    def __unicode__(self):
        return "Removing permission to old master disk..."

    def do(self):
        if self.is_database_instance:
            super(RemoveAccessRecreateSlave, self).undo()

    def undo(self):
        if self.is_database_instance:
            super(RemoveAccessRecreateSlave, self).do()


class RemoveAccessMigrate(AddAccessMigrate):
    def __unicode__(self):
        return "Removing permission to old disk..."

    def do(self):
        return super(RemoveAccessMigrate, self).undo()

    def undo(self):
        return super(RemoveAccessMigrate, self).do()


class AddHostsAllowMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Adding network on hosts_allow file..."

    @property
    def original_host(self):
        return self.host_migrate.host.address

    def _do_hosts_allow(self, func):
        script = func(
            self.original_host.address,
        )

        self.run_script(script)

    def add_hosts_allow(self):
        self._do_hosts_allow(
            self.get_add_hosts_allow_command
        )

    def remove_hosts_allow(self):
        self._do_hosts_allow(
            self.get_remove_hosts_allow_command
        )

    def do(self):
        self.add_hosts_allow()

    def undo(self):
        self.remove_hosts_allow()


class AddHostsAllowDatabaseMigrate(AddHostsAllowMigrate):
    @property
    def original_host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname


class CreatePubKeyMigrate(VolumeProviderBase):

    def __unicode__(self):
        return "Creating pubblic key..."

    @property
    def original_host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname

    def _do_pub_key(self, func):
        script = func(
            self.original_host.address
        )

        return self.run_script(script, host=self.original_host)

    @property
    def environment(self):
        return self.infra.environment

    def create_pub_key(self):
        output = self._do_pub_key(
            self.get_create_pub_key_command
        )
        pub_key = output['stdout'][0]
        script = 'echo "{}" >> ~/.ssh/authorized_keys'.format(pub_key)
        self.run_script(script)

    def remove_pub_key(self):
        self._do_pub_key(
            self.get_remove_pub_key_command
        )

    def do(self):
        return self.create_pub_key()

    def undo(self):
        self.remove_pub_key()


class RemovePubKeyMigrate(CreatePubKeyMigrate):

    def __unicode__(self):
        return "Removing pubblic key..."

    def do(self):
        self.remove_pub_key()

    def undo(self):
        self.create_pub_key()


class RemoveHostsAllowMigrate(AddHostsAllowMigrate):

    def __unicode__(self):
        return "Removing network from hosts_allow file..."

    def do(self):
        self.remove_hosts_allow()

    def undo(self):
        self.add_hosts_allow()


class RemoveHostsAllowDatabaseMigrate(RemoveHostsAllowMigrate):
    @property
    def original_host(self):
        master_instance = self.driver.get_master_instance()
        return self.infra.instances.exclude(
            id=master_instance.id
        ).first().hostname


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


class WaitSnapshotAvailableMigrate(VolumeProviderBase):
    ATTEMPTS = 60
    DELAY = 5

    def __unicode__(self):
        return "Wait snapshot available..."

    @property
    def environment(self):
        return self.infra.environment

    def waiting_be(self, state, snapshot):
        for _ in range(self.ATTEMPTS):
            snapshot_state = self.get_snapshot_state(snapshot)
            if snapshot_state == state:
                return True
            sleep(self.DELAY)
        raise EnvironmentError("Snapshot {} is {} should be {}".format(
            snapshot, state, snapshot_state
        ))

    @property
    def snapshot(self):
        if self.host_migrate and self.host_migrate.database_migrate:
            return self.host_migrate.database_migrate.host_migrate_snapshot
        else:
            return self.step_manager.snapshot

    def do(self):
        if self.is_database_instance:
            self.waiting_be('available', self.snapshot)


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
            self.destroy_volume(volume)

    def undo(self):
        raise NotImplementedError
