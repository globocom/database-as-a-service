# encoding: utf-8
from django_services import admin
from ..service.environment import EnvironmentService


class EnvironmentAdmin(admin.DjangoServicesAdmin):
    service_class = EnvironmentService
    search_fields = ("name", )
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True

