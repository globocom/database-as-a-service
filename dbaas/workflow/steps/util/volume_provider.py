from datetime import datetime
from requests import post, delete, get
from backup.models import Snapshot
from dbaas_credentials.models import CredentialType
from util import get_credentials_for, exec_remote_command_host
from physical.models import Volume
from base import BaseInstanceStep


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
    def provider(self):
        return self.credential.project

    @property
    def base_url(self):
        return "{}/{}/{}/".format(
            self.credential.endpoint, self.provider, self.environment
        )

    def create_volume(self, group, size_kb, to_address):
        url = self.base_url + "volume/new"
        data = {
            "group": group,
            "size_kb": size_kb,
            "to_address": to_address
        }

        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        volume = Volume()
        volume.host = self.host
        volume.identifier = response.json()['identifier']
        volume.total_size_kb = self.infra.disk_offering.size_kb
        volume.save()
        return volume

    def destroy_volume(self, volume):
        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)
        volume.delete()

    def get_path(self, volume):
        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = get(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['path']

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
        response = post(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

    def delete_snapshot(self, snapshot):
        url = "{}snapshot/{}".format(self.base_url, snapshot.snapshopt_id)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()

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

    def get_mount_command(self, volume):
        url = "{}commands/{}/mount".format(self.base_url, volume.identifier)
        response = get(url)
        if not response.ok:
            raise IndexError(response.content, response)
        return response.json()['command']

    def get_umount_command(self, volume):
        url = "{}commands/{}/umount".format(self.base_url, volume.identifier)
        response = get(url)
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


class NewVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Creating Volume..."

    def do(self):
        if not self.instance.is_database:
            return
        self.create_volume(
            self.infra.name, self.disk_offering.size_kb, self.host.address
        )

    def undo(self):
        if not self.instance.is_database:
            return

        for volume in self.host.volumes.all():
            self.add_access(volume, self.host)
            self.clean_up(volume)
            self.destroy_volume(volume)


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
