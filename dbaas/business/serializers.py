from django_services.api import DjangoServiceSerializer
from .models import Product, Plan


class ProductSerializer(DjangoServiceSerializer):

    class Meta:
        model = Product


class PlanSerializer(DjangoServiceSerializer):

    class Meta:
        model = Plan
