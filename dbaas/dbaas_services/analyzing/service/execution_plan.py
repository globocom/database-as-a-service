from django_services import service
from dbaas_services.analyzing.models import ExecutionPlan


class ExecutionPlanService(service.CRUDService):
    model_class = ExecutionPlan
