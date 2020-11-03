import logging
from time import sleep
from django.template.loader import render_to_string

from base import BaseInstanceStep
from plan import PlanStepNewInfra
from physical.models import Host
from workflow.steps.util.volume_provider import VolumeProviderBase
from workflow.steps.util.host_provider import CreateVirtualMachine, Provider as HostProvider


LOG = logging.getLogger(__name__)


class BaseK8SStep(BaseInstanceStep):

    @property
    def _verify_ssl(self):
        verify_ssl = self.headers.get("K8S-Verify-Ssl", 'false')
        return verify_ssl != 'false' and verify_ssl != 0

    @property
    def volume_provider(self):
        return VolumeProviderBase(self.instance)

    @property
    def host_provider(self):
        return HostProvider(self.instance, self.environment)


class NewVolumeK8S(BaseK8SStep):

    def __unicode__(self):
        return "Creating Volume..."

    def do(self):
        if not self.instance.is_database:
            return

        self.volume_provider.create_volume(
            self.infra.name,
            self.disk_offering.size_kb,
        )

    def undo(self):
        if not self.instance.is_database:
            return
        for volume in self.host.volumes.all():
            self.volume_provider.destroy_volume(volume)


class NewServiceK8S(BaseK8SStep):

    def __unicode__(self):
        return "Creating Service on kubernetes..."

    RETRIES = 30

    def do(self):
        self.host_provider.prepare()

    def undo(self):
        for attempt in range(self.RETRIES):
            try:
                self.host_provider.clean()
                break
            except Exception as e:
                if attempt == self.RETRIES - 1:
                    raise e
                sleep(10)
        host = self.instance.hostname
        host.delete()


class CreateConfigMap(BaseK8SStep, PlanStepNewInfra):

    def __unicode__(self):
        return "Creating config map..."

    def do(self):
        if not self.instance.is_database:
            return
        configuration = render_to_string(
            'physical/scripts/database_config_files/mongodb_40.conf',
            self.script_variables
        )
        self.host_provider.configure(configuration)

    def undo(self):
        if not self.instance.is_database:
            return
        self.host_provider.remove_configuration()


class UpdateHostMetadata(BaseK8SStep):
    def __unicode__(self):
        return "Update address of instance and host with pod ip..."

    def do(self):
        info = self.host_provider.host_info(self.host, refresh=True)
        self.instance.address = info["address"]
        self.instance.port = self.driver.default_port
        host = self.host
        host.address = self.instance.address
        host.save()

    def undo(self):
        self.do()


class NewPodK8S(BaseK8SStep, CreateVirtualMachine):
    def __unicode__(self):
        return "Creating POD on kubernetes..."

    def do(self):
        if not self.instance.is_database:
            return
        self.host_provider.create_host(
            self.infra, self.offering, self.instance.vm_name, self.team,
            port=self.instance.port, volume_name=self.host.volumes.last().identifier,
            host_obj=self.host
        )

    def undo(self):
        self.host_provider.destroy_host(self.host)


class CreateHostMetadata(BaseK8SStep):
    def __unicode__(self):
        return "Create host metadata on database..."

    def do(self):
        host = Host()
        host.address = self.instance.vm_name
        host.hostname = self.instance.vm_name
        host.user = 'TODO'
        host.password = 'TODO'
        host.provider = 'k8s'
        host.save()
        self.instance.hostname = host
        self.instance.save()

    def undo(self):
        pass
