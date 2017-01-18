from django_services import service
from ..models import DatabaseUpgrade


class DatabaseUpgradeService(service.CRUDService):
    model_class = DatabaseUpgrade
