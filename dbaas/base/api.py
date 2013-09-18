from django_services.api import DjangoServiceAPI, register

from .service.environment import EnvironmentService
from .service.node import NodeService
from .service.instance import InstanceService
from .service.database import DatabaseService
from .service.credential import CredentialService
from .serializers import EnvironmentSerializer, NodeSerializer, InstanceSerializer, DatabaseSerializer, CredentialSerializer


class EnvironmentAPI(DjangoServiceAPI):
    serializer_class = EnvironmentSerializer
    service_class = EnvironmentService


class NodeAPI(DjangoServiceAPI):
    serializer_class = NodeSerializer
    service_class = NodeService


class InstanceAPI(DjangoServiceAPI):

    serializer_class = InstanceSerializer
    service_class = InstanceService
    operations = ('list', 'retrieve', 'create', 'update', 'destroy')


class DatabaseAPI(DjangoServiceAPI):
    serializer_class = DatabaseSerializer
    service_class = DatabaseService


class CredentialAPI(DjangoServiceAPI):
    serializer_class = CredentialSerializer
    service_class = CredentialService


register('environment', EnvironmentAPI)
register('node', NodeAPI)
register('instance', InstanceAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)

