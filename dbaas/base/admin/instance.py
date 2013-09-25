# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.instance import InstanceService

class InstanceAdmin(admin.DjangoServicesAdmin):
    service_class = InstanceService
    search_fields = ("name", "user", "product__name", "node__address")
    list_display = ("name", "user", "node", "product")
    list_filter = ("node__environment", "product", "engine", "plan")
    save_on_top = True

