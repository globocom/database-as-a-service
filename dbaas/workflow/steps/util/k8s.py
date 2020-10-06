import logging

import yaml
from django.template.loader import render_to_string
from kubernetes.client import Configuration, ApiClient, CoreV1Api
from dbaas_credentials.models import CredentialType

from base import BaseInstanceStep
from plan import PlanStepNewInfra
from physical.models import Host
from util import get_credentials_for
from workflow.steps.util.volume_provider import VolumeProviderBase
from workflow.steps.util.host_provider import Provider as HostProvider


LOG = logging.getLogger(__name__)


class BaseK8SStep(BaseInstanceStep):

    def hostname(self):
        if self.host and self.hostname:
            hostname = self.host.hostname
        else:
            hostname = self.instance.vm_name
        return hostname

    @property
    def namespace(self):
        return 'default'

    @property
    def volume_path_root(self):
        return '/data'

    @property
    def volume_path_db(self):
        return '{}/db'.format(self.volume_path_root)

    @property
    def database_log_dir(self):
        return '{}/logs'.format(self.volume_path_root)

    @property
    def database_log_file_name(self):
        return 'mongodb.log'

    @property
    def database_log_full_path(self):
        return '{}/{}'.format(
            self.database_log_dir, self.database_log_file_name
        )

    @property
    def database_config_name(self):
        return 'mongodb.conf'

    @property
    def database_config_full_path(self):
        return '{}/{}'.format(self.volume_path_root, self.database_config_name)

    @property
    def label_name(self):
        return self.infra.name

    @property
    def service_name(self):
        return 'service-{}'.format(
            self.hostname().split('.')[0]
        )

    @property
    def statefulset_name(self):
        return self.hostname().split('.')[0]

    @property
    def pod_name(self):
        return '{}-0'.format(self.statefulset_name)

    @property
    def config_map_name(self):
        return 'configmap-{}'.format(self.hostname())

    @property
    def client_class_name(self):
        return "CoreV1Api"

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                environment=self.environment,
                credential_type=CredentialType.KUBERNETES)
        return self._credential

    @property
    def client(self):
        configuration = Configuration()
        configuration.api_key['authorization'] = "Bearer {}".format(self.headers['K8S-Token'])
        configuration.host = self.headers['K8S-Endpoint']
        configuration.verify_ssl = self._verify_ssl
        api_client = ApiClient(configuration)
        return CoreV1Api(api_client)

    @property
    def _verify_ssl(self):
        verify_ssl = self.headers.get("K8S-Verify-Ssl", 'false')
        return verify_ssl != 'false' and verify_ssl != 0

    @property
    def template_path(self):
        raise NotImplementedError('U must set template path')

    @property
    def context(self):
        return {}

    @property
    def yaml_file(self):
        yaml_file = render_to_string(
            self.template_path,
            self.context
        )
        return yaml.safe_load(yaml_file)

    def do(self):
        pass

    def undo(self):
        pass


class NewVolumeK8S(BaseK8SStep):

    def __unicode__(self):
        return "Creating Volume..."

    @property
    def provider(self):
        return VolumeProviderBase(self.instance)

    @property
    def has_snapshot_on_step_manager(self):
        return (self.host_migrate and hasattr(self, 'step_manager')
                and self.host_migrate == self.step_manager)

    def _remove_volume(self, volume):
        self.provider.destroy_volume(volume)

    def do(self):
        if not self.instance.is_database:
            return

        self.provider.create_volume(
            self.infra.name,
            self.disk_offering.size_kb,
        )

    def undo(self):
        if not self.instance.is_database:
            return
        for volume in self.host.volumes.all():
            self._remove_volume(volume)


class NewServiceK8S(BaseK8SStep):

    def __unicode__(self):
        return "Creating Service on kubernetes..."

    def do(self):
        provider = HostProvider(self.instance, self.environment)
        provider.prepare()

    def undo(self):
        provider = HostProvider(self.instance, self.environment)
        provider.clean()


class CreateConfigMap(PlanStepNewInfra):

    def __unicode__(self):
        return "Creating config map..."

    def do(self):
        if not self.instance.is_database:
            return
        configuration = render_to_string(
            'physical/scripts/database_config_files/mongodb_40.conf',
            self.script_variables
        )
        provider = HostProvider(self.instance, self.environment)
        provider.configure(configuration)

    def undo(self):
        if not self.instance.is_database:
            return
        provider = HostProvider(self.instance, self.environment)
        provider.remove_configuration()


class UpdateHostMetadata(BaseK8SStep):
    def __unicode__(self):
        return "Update address of instance and host with pod ip..."

    def do(self):
        provider = HostProvider(self.instance, self.environment)
        info = provider.host_info(self.host, refresh=True)
        self.instance.address = info["address"]
        self.instance.port = self.driver.default_port
        host = self.host
        host.address = self.instance.address
        host.save()


class NewPodK8S(BaseK8SStep):
    def __unicode__(self):
        return "Creating POD on kubernetes..."

    @property
    def provider(self):
        return HostProvider(self.instance, self.environment)

    @property
    def template_path(self):
        return 'physical/scripts/k8s/pod.yaml'

    @property
    def config_map_mount_path(self):
        return '/mnt/config-map'

    @property
    def context(self):
        return {
            'STATEFULSET_NAME': self.statefulset_name,
            'POD_NAME': self.pod_name,
            'LABEL_NAME': self.label_name,
            'SERVICE_NAME': self.service_name,
            'INIT_CONTAINER_CREATE_CONFIG_COMMANDS': (
                'cp {}/{} {}; chown mongodb:mongodb {}'.format(
                    self.config_map_mount_path,
                    self.database_config_name,
                    self.volume_path_root,
                    self.database_config_full_path
                )
            ),
            'CONFIG_MAP_MOUNT_PATH': self.config_map_mount_path,
            'IMAGE_NAME': 'mongo',
            'IMAGE_TAG': '4.2',
            'CONTAINER_PORT': 27017,  # self.instance.port
            'VOLUME_NAME': 'data-volume',
            'VOLUME_PATH_ROOT': '/data',
            'VOLUME_PATH_DB': '/data/db',
            'VOLUME_PATH_CONFIGDB': '/data/configdb',
            'CPU': 100,
            'MEMORY': 200,
            'CPU_LIMIT': 200,
            'MEMORY_LIMIT': 400,
            'VOLUME_CLAIM_NAME': self.latest_disk.identifier,
            'CONFIG_MAP_NAME': self.config_map_name,
            'CONFIG_FILE_NAME': self.database_config_name,
            'DATABASE_LOG_DIR': self.database_log_dir,
            'DATABASE_CONFIG_FULL_PATH': self.database_config_full_path,
            'DATABASE_LOG_FULL_PATH': self.database_log_full_path
        }

    @property
    def team(self):
        if self.has_database:
            return self.database.team.name
        elif self.create:
            return self.create.team.name
        elif (self.step_manager
              and hasattr(self.step_manager, 'origin_database')):
            return self.step_manager.origin_database.team.name

    @property
    def stronger_offering(self):
        return self.plan.stronger_offering

    @property
    def weaker_offering(self):
        return self.plan.weaker_offering

    @property
    def database_offering(self):
        if self.host_migrate and self.host_migrate.database_migrate:
            return self.host_migrate.database_migrate.offering
        if self.has_database:
            return self.infra.offering
        return self.stronger_offering

    @property
    def offering(self):
        if self.instance.is_database:
            return self.database_offering
        return self.weaker_offering

    def update_databaseinfra_last_vm_created(self):
        last_vm_created = self.infra.last_vm_created
        last_vm_created += 1
        self.infra.last_vm_created = last_vm_created
        self.infra.save()

    def delete_instance(self):
        if self.instance.id:
            self.instance.delete()

    def do(self):
        if not self.instance.is_database:
            return
        self.provider.create_host(
            self.infra, self.offering, self.instance.vm_name, self.team,
            zone=None, yaml_context=self.context, host_obj=self.host
        )

    def undo(self):
        self.provider.destroy_host(self.host)


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
        host.offering = None
        host.save()
        self.instance.hostname = host
        self.instance.save()
