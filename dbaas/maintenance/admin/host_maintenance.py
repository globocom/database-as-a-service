# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from ..service.host_maintenance import HostMaintenanceService
from ..forms import HostMaintenanceForm
import logging
from django.contrib import messages
LOG = logging.getLogger(__name__)
from .. import models
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

class HostMaintenanceAdmin(admin.DjangoServicesAdmin):
    
    actions = None
    
    service_class = HostMaintenanceService
    search_fields = ("maintenance__description", "host__hostname", "status")
    list_display = ("maintenance", "host", "started_at", "finished_at", "status")
    fields = ("maintenance", "host", "status", "started_at", "finished_at", "main_log", "rollback_log")
    readonly_fields = fields
    #save_on_top = True
    form = HostMaintenanceForm
    
    ordering = ["-started_at"]

    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False




