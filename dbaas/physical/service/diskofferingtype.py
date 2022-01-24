from django_services import service
from ..models import DiskOfferingType


class DiskOfferingTypeService(service.CRUDService):
    model_class = DiskOfferingType
