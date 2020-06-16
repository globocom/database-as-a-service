from time import sleep
import logging
import json

import yaml
from django.template.loader import render_to_string

from base import BaseInstanceStep
from physical.models import Volume, Host

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
    def context(self):
        return {
            'POD_NAME': self.statefulset_name,
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
    interval = 10

    def __unicode__(self):
        return "Waiting POD be ready..."

    def do(self):
        for attempt in range(self.retries):
            pod_data = self.client.read_namespaced_pod_status(
                self.pod_name, self.namespace
            )
            for status_data in pod_data.status.conditions:
                if status_data.type != 'Ready':
                    continue
                else:
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
