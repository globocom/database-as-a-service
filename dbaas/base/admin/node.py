# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.node import NodeService


class NodeAdmin(admin.DjangoServicesAdmin):
    service_class = NodeService
    search_fields = ("address", "port", "instance__name", "environment__name")
    list_display = ("address", "port", "is_active", "instance", "environment",)
    list_filter = ("is_active", "environment", "instance")
    save_on_top = True
