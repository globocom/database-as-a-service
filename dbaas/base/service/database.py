from django_services import service
from ..models import Database


class DatabaseService(service.CRUDService):
    model_class = Database
