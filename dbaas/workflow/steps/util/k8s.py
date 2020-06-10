import yaml
from django.template.loader import render_to_string
from base import BaseInstanceStep
from physical.models import Volume


class BaseK8SStep(BaseInstanceStep):

    @property
    def label_name(self):
        return self.infra.name

    @property
    def service_name(self):
        return 'service-{}'.format(
            self.host.hostname.split('.')[0]
        )

    @property
    def volume_claim_name(self):
        return 'pvc-{}'.format(self.host.hostname)

    @property
    def pod_name(self):
        return 'pod-{}'.format(self.host.hostname.split('.')[0])

    @property
    def client_class_name(self):
        return "CoreV1Api"

    @property
    def client(self):
        from kubernetes import client, config
        config.load_kube_config(
            '/Users/rafael.goncalves/.kube/configRANCHER'
        )

        return getattr(client, self.client_class_name)()

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
            self.volume_claim_name, 'default'
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
            'default', self.yaml_file
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
            'NODE_PORT': 30021
        }

    def do(self):
        if not self.instance.is_database:
            return

        self.client.create_namespaced_service(
            'default', self.yaml_file
        )

    def undo(self):
        self.client.delete_namespaced_service(
            self.service_name,
            'default'
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
    def context(self):
        return {
            'POD_NAME': self.pod_name,
            'LABEL_NAME': self.label_name,
            'SERVICE_NAME': self.service_name,
            'IMAGE_NAME': 'mongo',
            'IMAGE_TAG': '4.2',
            'CONTAINER_PORT': 27017,  # self.instance.port
            'VOLUME_NAME': 'data-volume',
            'VOLUME_PATH': '/data/db',
            'CPU': 100,
            'MEMORY': 200,
            'CPU_LIMIT': 200,
            'MEMORY_LIMIT': 400,
            'VOLUME_CLAIM_NAME': self.volume_claim_name
        }

    def do(self):
        if not self.instance.is_database:
            return

        self.client.create_namespaced_stateful_set(
            'default', self.yaml_file
        )

    def undo(self):
        self.client.delete_namespaced_stateful_set(
            self.pod_name,
            'default',
            orphan_dependents=False
        )
