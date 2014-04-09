from django_services import service
from ..models import IntegrationType


class IntegrationTypeService(service.CRUDService):
    model_class = IntegrationType