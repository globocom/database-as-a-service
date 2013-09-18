# encoding: utf-8
from django_services import admin
from ..service.engine import EngineService

class EngineAdmin(admin.DjangoServicesAdmin):
    service_class = EngineService
    search_fields = ["engine_type__name", ]
    list_display = ("engine_type", "version", )
    save_on_top = True