# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.database import DatabaseService


class DatabaseAdmin(admin.DjangoServicesAdmin):
    service_class = DatabaseService
    search_fields = ("name", "instance__name")
    list_display = ("name", "instance",)
