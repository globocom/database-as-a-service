from django_services import service
from ..models import TaskSchedule


class TaskScheduleService(service.CRUDService):
    model_class = TaskSchedule
