from django_services import service
from ..models import Team


class TeamService(service.CRUDService):
    model_class = Team
