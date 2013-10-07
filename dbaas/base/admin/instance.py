# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django_services import admin
from ..service.instance import InstanceService
from ..models import Node


class NodeAdmin(django_admin.TabularInline):
    model = Node
    list_display = ("address", "port", "is_active",)


class InstanceAdmin(admin.DjangoServicesAdmin):
    service_class = InstanceService
    search_fields = ("name", "user", "product__name", "nodes__address",)
    list_display = ("name", "user", "node", "product")
    list_filter = ("environment", "product", "engine", "plan")
    save_on_top = True

    inlines = [
        NodeAdmin
    ]

