from requests import post, delete, get
from dbaas_credentials.models import CredentialType
from physical.models import Volume
from util import get_credentials_for
from base import BaseInstanceStep
from util import exec_remote_command_host
import logging

LOG = logging.getLogger(__name__)

class VolumeProviderBase(BaseInstanceStep):

    def __init__(self, instance):
        super(VolumeProviderBase, self).__init__(instance)
        self._credential = None

    @property
    def credential(self):
        # TODO Remove hard coded "faas"
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.VOLUME_PROVIDER,
                project="faas"
            )
        return self._credential

    @property
    def volume(self):
        return self.host.volumes.first()

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


class NewVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Creating Volume..."

    def do(self):

        if not self.host.database_instance():
            return

        self.create_volume(
            self.infra.name, self.disk_offering.size_kb, self.host.address
        )

    def undo(self):

        if not self.host.database_instance():
            return

        volume = self.volume
        if not volume:
            return

        script = "rm -rf /data/*"
        self.run_script(script)

        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)

        volume.delete()


class MountDataVolume(VolumeProviderBase):
    def __unicode__(self):
        return "Mounting data volume..."

    def do(self):

        if not self.host.database_instance():
            return

        url = "{}commands/{}/mount".format(
            self.base_url, self.volume.identifier)

        response = get(url)
        if not response.ok:
            raise IndexError(response.content, response)

        script = response.json()['command']
        self.run_script(script)

    def undo(self):
        pass


class ResizeVolume(VolumeProviderBase):
    def __unicode__(self):
        return "Resizing data volume..."

    def do(self):

        if not self.host.database_instance():
            return

        volume = self.volume

        url = "{}resize/{}".format(self.base_url, volume.identifier)

        data = {
            "new_size_kb": self.infra.disk_offering.size_kb,
        }

        response = post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        volume.total_size_kb = self.infra.disk_offering.size_kb
        volume.save()

        LOG.info('{} Volume saved {}'.format(volume.host, volume.total_size_kb))
        LOG.info("{}, {}".format(self.infra.disk_offering.size_kb, volume.total_size_kb))

    def undo(self):
        pass
