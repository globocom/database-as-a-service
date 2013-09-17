
from django_services import service
from .models import Instance

class InstanceService(service.CRUDService):
    model_class = Instance
