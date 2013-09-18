# encoding: utf-8
from django_services import admin
from ..service.instance import InstanceService

class InstanceAdmin(admin.DjangoServicesAdmin):
    service_class = InstanceService
    search_fields = ["name", "user", "product__name", "node__address"]
    list_display = ("name", "user", "node", "product")
    save_on_top = True

