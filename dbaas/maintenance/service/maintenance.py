from django_services import service
from .. import models


class MaintenanceService(service.CRUDService):
    model_class = models.Maintenance
