from django_services import service
from ..models import Plan


class PlanService(service.CRUDService):
    model_class = Plan
    # PlanAttribute is part of Plan
