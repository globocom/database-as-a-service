from django_services import service
from .. import models


class ProductService(service.CRUDService):
    model_class = models.Product
