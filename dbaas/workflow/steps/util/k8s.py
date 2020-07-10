from time import sleep
import logging
import json

import yaml
from django.template.loader import render_to_string
from kubernetes import client, config
from dbaas_credentials.models import CredentialType

from base import BaseInstanceStep
from physical.models import Volume, Host, Offering
from util import get_credentials_for
from physical.configurations import configuration_factory


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
    def volume_claim_name(self):
        return 'pvc-{}'.format(self.hostname())

    @property
    def statefulset_name(self):
        return 'pod-{}'.format(self.hostname().split('.')[0])

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
        config.load_kube_config(
            self.credential.get_parameter_by_name('kube_config_path')
        )

        conf = client.configuration.Configuration()
        conf.verify_ssl = False

        return getattr(client, self.client_class_name)(client.ApiClient(conf))

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
    def active_volume(self):
        return False

    @property
    def has_snapshot_on_step_manager(self):
        return (self.host_migrate and hasattr(self, 'step_manager')
                and self.host_migrate == self.step_manager)

    def _remove_volume(self, volume):
        self.client.delete_namespaced_persistent_volume_claim(
            self.volume_claim_name, self.namespace
        )
        volume.delete()

    @property
    def template_path(self):
        return 'physical/scripts/k8s/persistence_volume_claim.yaml'

    @property
    def context(self):
        return {
            'STORAGE_NAME': self.volume_claim_name,
            'STORAGE_SIZE': 2
        }

    def do(self):
        if not self.instance.is_database:
            return

        self.client.create_namespaced_persistent_volume_claim(
            self.namespace, self.yaml_file
        )
        volume = Volume()
        volume.host = self.host
        volume.identifier = self.context['STORAGE_NAME']
        volume.total_size_kb = self.infra.disk_offering.size_kb
        volume.is_active = self.active_volume
        volume.save()

    def undo(self):
        if not self.instance.is_database or not self.host:
            return
        volume = Volume.objects.get(
            identifier=self.volume_claim_name, host=self.host
        )
        self._remove_volume(volume)


class NewServiceK8S(BaseK8SStep):
    def __unicode__(self):
        return "Creating Service on kubernetes..."

    @property
    def template_path(self):
        return 'physical/scripts/k8s/service.yaml'

    @property
    def context(self):
        return {
            'SERVICE_NAME': self.service_name,
            'LABEL_NAME': self.label_name,
            'INSTANCE_PORT': 27017,  # self.instance.port,
            # 'NODE_PORT': 30022
        }

    def do(self):
        if not self.instance.is_database:
            return

        self.client.create_namespaced_service(
            self.namespace, self.yaml_file
        )

    def undo(self):
        self.client.delete_namespaced_service(
            self.service_name,
            self.namespace
        )


class NewPodK8S(BaseK8SStep):
    def __unicode__(self):
        return "Creating POD on kubernetes..."

    @property
    def client_class_name(self):
        return "AppsV1beta1Api"

    @property
    def template_path(self):
        return 'physical/scripts/k8s/pod.yaml'

    @property
    def config_map_mount_path(self):
        return '/mnt/config-map'

    @property
    def context(self):
        return {
            'POD_NAME': self.statefulset_name,
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
            'VOLUME_CLAIM_NAME': self.volume_claim_name,
            'CONFIG_MAP_NAME': self.config_map_name,
            'CONFIG_FILE_NAME': self.database_config_name,
            'DATABASE_LOG_DIR': self.database_log_dir,
            'DATABASE_CONFIG_FULL_PATH': self.database_config_full_path,
            'DATABASE_LOG_FULL_PATH': self.database_log_full_path
        }

    def do(self):
        if not self.instance.is_database:
            return
        self.client.create_namespaced_stateful_set(
            self.namespace, self.yaml_file
        )

    def undo(self):
        self.client.delete_namespaced_stateful_set(
            self.statefulset_name,
            self.namespace,
            orphan_dependents=False
        )


class WaitingPodBeReady(BaseK8SStep):
    retries = 30
    interval = 1

    def __unicode__(self):
        return "Waiting POD be ready..."

    def do(self):
        for attempt in range(self.retries):
            pod_data = self.client.read_namespaced_pod_status(
                self.pod_name, self.namespace
            )
            for status_data in pod_data.status.conditions:
                if status_data.type == 'Ready':
                    if status_data.status == 'True':
                        return True
            if attempt == self.retries - 1:
                LOG.error("Maximum number of login attempts.")
                raise EnvironmentError('POD {} is not ready'.format(
                    self.pod_name
                ))

            LOG.warning("Pod {} not ready.".format(self.pod_name))
            LOG.info("Wating %i seconds to try again..." % (self.interval))
            sleep(self.interval)


class SetServiceEndpoint(BaseK8SStep):
    def __unicode__(self):
        return "Update instance with service address and port..."

    def service_metadata(self):
        return self.client.read_namespaced_service(
            self.service_name, self.namespace
        )

    def do(self):
        service_metadata = self.service_metadata()
        service_annotations = json.loads(
            service_metadata.metadata.annotations[
                'field.cattle.io/publicEndpoints'
            ]
        )
        # TODO: Validate is here the instance already saved on database
        if service_annotations:
            service_annotations = service_annotations[0]
        self.instance.address = service_annotations['addresses'][0]
        self.instance.port = service_annotations['port']
        # self.instance.save()
        host = Host()
        host.address = self.instance.address
        host.hostname = self.instance.vm_name
        host.user = 'TODO'
        host.password = 'TODO'
        host.provider = 'k8s'
        host.identifier = self.pod_name
        host.offering = None
        host.save()
        self.instance.hostname = host
        self.instance.save()


class NewConfigMapK8S(BaseK8SStep):
    def __unicode__(self):
        return "Creating config map..."

    @property
    def database(self):
        from logical.models import Database
        if self.infra.databases.exists():
            return self.infra.databases.first()
        database = Database()
        step_manager = self.infra.databases_create.last()
        database.name = (step_manager.name
                         if step_manager else self.step_manager.name)
        return database

    @property
    def template_path(self):
        return 'physical/scripts/k8s/config_map.yaml'

    @property
    def context(self):
        return {
            'CONFIG_MAP_NAME': self.config_map_name,
            'CONFIG_MAP_LABEL': self.label_name,
            'CONFIG_FILE_NAME': self.database_config_name,
            'CONFIG_CONTENT': 'config_content'
        }

    @property
    def script_variables(self):
        variables = {
            'DATABASENAME': self.database.name,
            'DBPASSWORD': self.infra.password,
            'HOST': self.host.hostname.split('.')[0],
            # 'HOSTADDRESS': self.instance.address,
            'ENGINE': self.plan.engine.engine_type.name,
            'MOVE_DATA': (
                bool(self.upgrade) or
                bool(self.reinstall_vm) or
                bool(self.engine_migration)
            ),
            'DRIVER_NAME': self.infra.get_driver().topology_name(),
            'DISK_SIZE_IN_GB': (self.disk_offering.size_gb()
                                if self.disk_offering else 8),
            'ENVIRONMENT': self.environment,
            'HAS_PERSISTENCE': self.infra.plan.has_persistence,
            'IS_READ_ONLY': self.instance.read_only,
            'SSL_CONFIGURED': self.infra.ssl_configured,
            'DATABASE_LOG_FULL_PATH': self.database_log_full_path,
            'VOLUME_PATH_ROOT': self.volume_path_root,
            'VOLUME_PATH_DB': self.volume_path_db
        }

        if self.infra.ssl_configured:
            from workflow.steps.util.ssl import InfraSSLBaseName
            from workflow.steps.util.ssl import InstanceSSLBaseName
            infra_ssl = InfraSSLBaseName(self.instance)
            instance_ssl = InstanceSSLBaseName(self.instance)
            variables['INFRA_SSL_CA'] = infra_ssl.ca_file_path
            variables['INFRA_SSL_CERT'] = infra_ssl.cert_file_path
            variables['INFRA_SSL_KEY'] = infra_ssl.key_file_path
            variables['INSTANCE_SSL_CA'] = instance_ssl.ca_file_path
            variables['INSTANCE_SSL_CERT'] = instance_ssl.cert_file_path
            variables['INSTANCE_SSL_KEY'] = instance_ssl.key_file_path

        variables['configuration'] = self.get_configuration()
        variables['GRAYLOG_ENDPOINT'] = self.get_graylog_config()

        return variables

    def get_graylog_config(self):
        credential = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.GRAYLOG
        )
        return credential.get_parameter_by_name('endpoint_log')

    @property
    def offering(self):
        if self.resize:
            return self.resize.target_offer

        try:
            return self.infra.offering
        except Offering.DoesNotExist:
            return self.instance.offering

    def get_configuration(self):
        try:
            configuration = configuration_factory(
                self.infra, self.offering.memory_size_mb
            )
        except NotImplementedError:
            return None
        else:
            return configuration

    def do(self):
        if not self.instance.is_database:
            return

        yaml_file = self.yaml_file
        yaml_file['data']['mongodb.conf'] = render_to_string(
            'physical/scripts/database_config_files/mongodb_40.conf',
            self.script_variables
        )
        self.client.create_namespaced_config_map(
            self.namespace, yaml_file
        )

    def undo(self):
        self.client.delete_namespaced_config_map(
            self.config_map_name,
            self.namespace
        )
