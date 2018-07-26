from django_services import service
from ..models import Offering


class OfferingService(service.CRUDService):
    model_class = Offering
