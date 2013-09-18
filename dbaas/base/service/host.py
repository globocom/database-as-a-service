from django_services import service
from ..models import Node


class NodeService(service.CRUDService):
    model_class = Node
