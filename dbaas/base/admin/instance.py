# encoding: utf-8
from django_services import admin
from ..service.instance import InstanceService

class InstanceAdmin(admin.DjangoServicesAdmin):
    service_class = InstanceService
    search_fields = ["name"]

