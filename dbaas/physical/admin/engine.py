# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.engine import EngineService


class EngineAdmin(admin.DjangoServicesAdmin):
    service_class = EngineService
    search_fields = ("engine_type__name",)
    list_display = ("engine_type", "version", )
    list_filter = ("engine_type",)
    save_on_top = True
