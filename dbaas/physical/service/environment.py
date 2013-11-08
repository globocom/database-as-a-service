from django_services import service
from ..models import Environment


class EnvironmentService(service.CRUDService):
    model_class = Environment
