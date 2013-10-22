from django_services import service
from . import models


class BindService(service.CRUDService):
    model_class = models.Bind