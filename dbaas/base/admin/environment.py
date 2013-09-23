# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.environment import EnvironmentService


class EnvironmentAdmin(admin.DjangoServicesAdmin):
    service_class = EnvironmentService
    search_fields = ("name", )
    list_filter = ("is_active", )
    list_display = ("name", "is_active")
    save_on_top = True

