from requests import post, delete
from dbaas_credentials.models import CredentialType
from physical.models import Volume
from util import get_credentials_for
from base import BaseInstanceStep



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


class NewVolume(VolumeProviderBase):

    def __unicode__(self):
        return "Creating Volume..."

    def do(self):
        self.create_volume(
            self.infra.name, self.disk_offering.size_kb, self.host.addres
        )

    def undo(self):
        volume = self.volume
        if not volume:
            return

        url = "{}volume/{}".format(self.base_url, volume.identifier)
        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)

        volume.delete()
