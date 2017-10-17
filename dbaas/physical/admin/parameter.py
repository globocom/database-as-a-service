# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.parameter import ParameterService
from ..forms.parameter import ParameterForm


class ParameterAdmin(admin.DjangoServicesAdmin):
    form = ParameterForm
    service_class = ParameterService
    search_fields = ("name",)
    list_filter = ("engine_type", "dynamic", )
    list_display = ("name", "engine_type", "dynamic",
                    "parameter_type", "allowed_values", "description")
    save_on_top = True
