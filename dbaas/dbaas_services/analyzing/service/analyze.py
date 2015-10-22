from django_services import service
from dbaas_services.analyzing.models import AnalyzeRepository


class AnalyzeRepositoryService(service.CRUDService):
    model_class = AnalyzeRepository
