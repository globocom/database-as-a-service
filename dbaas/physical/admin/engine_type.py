# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.engine import EngineTypeService


class EngineTypeAdmin(admin.DjangoServicesAdmin):
    service_class = EngineTypeService
    search_fields = ("name",)
    list_filter = ("is_in_memory",)
    list_display = ("name", "is_in_memory", "created_at")
    save_on_top = True
