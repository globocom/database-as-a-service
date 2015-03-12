from django_services import service
from .. import models


class HostMaintenanceService(service.CRUDService):
    model_class = models.HostMaintenance
