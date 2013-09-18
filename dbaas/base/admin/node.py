# encoding: utf-8
from django_services import admin
from ..service.node import NodeService


class NodeAdmin(admin.DjangoServicesAdmin):
    service_class = NodeService
    search_fields = ["address", "port"]
    list_display = ("address", "port", "environment", "is_active")
    list_filter = ("is_active", )
    save_on_top = True
