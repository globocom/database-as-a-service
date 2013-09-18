# encoding: utf-8
from django_services import admin
from ..service import HostService


class HostAdmin(admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = ["fqdn"]
    list_display = ("fqdn", "environment", "is_active")
    list_filter = ("is_active", )
    save_on_top = True
