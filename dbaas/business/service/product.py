from django_services import service
from ..models import Product


class ProductService(service.CRUDService):
    model_class = Product
