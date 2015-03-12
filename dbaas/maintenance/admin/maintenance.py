# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin as django_admin
from django.utils.translation import ugettext_lazy as _
from django_services import admin
from ..service.maintenance import MaintenanceService



class MaintenanceAdmin(admin.DjangoServicesAdmin):
    service_class = MaintenanceService
    search_fields = ("scheduled_for", "description", "maximum_workers",)
    list_display = ("scheduled_for", "description", "maximum_workers",)
    save_on_top = True


