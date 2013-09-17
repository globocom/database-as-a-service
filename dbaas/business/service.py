
from django_services import service
from .models import Product, Plan


class ProductService(service.CRUDService):
    model_class = Product


class PlanService(service.CRUDService):
    model_class = Plan
    # PlanAttribute is part of Plan

