# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.host import HostService


class HostAdmin(admin.DjangoServicesAdmin):
    service_class = HostService
    search_fields = ("hostname",)
    list_display = ("hostname",)
    save_on_top = True
