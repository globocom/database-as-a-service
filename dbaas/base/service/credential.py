from django_services import service
from ..models import Credential


class CredentialService(service.CRUDService):
    model_class = Credential
    
