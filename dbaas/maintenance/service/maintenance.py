from django_services import service
from ..models import Maintenance


class MaintenanceService(service.CRUDService):
    model_class = Maintenance
