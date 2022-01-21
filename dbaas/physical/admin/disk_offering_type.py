# -*- coding: utf-8 -*-
#from django.contrib import admin
from django_services import admin as services_admin
from ..service.diskofferingtype import DiskOfferingTypeService


#class DiskOfferingTypeAdmin(admin.ModelAdmin):
class DiskOfferingTypeAdmin(services_admin.DjangoServicesAdmin):
    service_class = DiskOfferingTypeService
    search_fields = ('name', 'type', 'identifier')
    list_display = ('name', 'type', 'identifier', 'is_default', 'selected_environments')
    list_filter = ('name', 'type', 'identifier', 'is_default', 'environments')
    

    def selected_environments(self, obj):
        return ",".join(obj.environments.values_list('name', flat=True))

    save_on_top = True
    filter_horizontal = ("environments",)

