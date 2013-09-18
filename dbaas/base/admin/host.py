# encoding: utf-8
from django_services import admin
from ..service.node import NodeService


class NodeAdmin(admin.DjangoServicesAdmin):
    service_class = NodeService
    search_fields = ["fqdn"]
    list_display = ("fqdn", "environment", "is_active")
    list_filter = ("is_active", )
    save_on_top = True
