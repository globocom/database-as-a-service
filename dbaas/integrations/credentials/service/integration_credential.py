from django_services import service
from ..models import IntegrationCredential


class IntegrationCredentialService(service.CRUDService):
    model_class = IntegrationCredential