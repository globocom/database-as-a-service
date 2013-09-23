# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.node import NodeService


class NodeAdmin(admin.DjangoServicesAdmin):
    service_class = NodeService
    search_fields = ["address", "port"]
    list_display = ("address", "port", "environment", "is_active")
    list_filter = ("is_active", )
    save_on_top = True
