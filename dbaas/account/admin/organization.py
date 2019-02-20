# -*- coding: utf-8 -*-
from django.contrib import admin
import logging
from ..forms.role import RoleAdminForm


LOG = logging.getLogger(__name__)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "grafana_orgid", "grafana_hostgroup",
        "grafana_datasource", "grafana_endpoint", "external"]
    search_fields = ('name',)

