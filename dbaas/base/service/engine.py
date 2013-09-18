from django_services import service
from ..models import Engine


class EngineService(service.CRUDService):
    model_class = Engine