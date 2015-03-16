from django_services import service
from ..models import HostMaintenance


class HostMaintenanceService(service.CRUDService):
    model_class = HostMaintenance
