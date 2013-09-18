from django_services.api import DjangoServiceAPI, register

from .service.environment import EnvironmentService
from .service.host import HostService
from .service.instance import InstanceService
from .service.database import DatabaseService
from .service.credential import CredentialService
from .serializers import EnvironmentSerializer, HostSerializer, InstanceSerializer, DatabaseSerializer, CredentialSerializer


class EnvironmentAPI(DjangoServiceAPI):
    serializer_class = EnvironmentSerializer
    service_class = EnvironmentService


class HostAPI(DjangoServiceAPI):
    serializer_class = HostSerializer
    service_class = HostService


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
register('host', HostAPI)
register('instance', InstanceAPI)
register('database', DatabaseAPI)
register('credential', CredentialAPI)

