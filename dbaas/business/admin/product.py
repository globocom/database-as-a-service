# encoding: utf-8
from django_services import admin
from ..service.product import ProductService


class ProductAdmin(admin.DjangoServicesAdmin):
    service_class = ProductService
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "is_active", "slug")
