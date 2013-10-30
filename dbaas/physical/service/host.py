from django_services import service
from ..models import Host


class HostService(service.CRUDService):
    model_class = Host
    # PlanAttribute is part of Plan
