from django_services.api import DjangoServiceAPI, register
from .service import InstanceService
from .serializers import InstanceSerializer

class InstanceAPI(DjangoServiceAPI):

    serializer_class = InstanceSerializer
    service_class = InstanceService
    operations = ('list', 'retrieve', 'create', 'update', 'destroy')

register('instance', InstanceAPI)
