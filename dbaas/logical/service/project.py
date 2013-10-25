from django_services import service
from .. import models


class ProjectService(service.CRUDService):
    model_class = models.Project
