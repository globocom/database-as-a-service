# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.parameter import ParameterService


class ParameterAdmin(admin.DjangoServicesAdmin):
    service_class = ParameterService
    search_fields = ("name",)
    list_filter = ("engine_type",)
    list_display = ("name", "engine_type", "dynamic", "class_path")
    save_on_top = True
