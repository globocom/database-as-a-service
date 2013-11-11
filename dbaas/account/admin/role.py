# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging
from ..forms.role import RoleAdminForm


LOG = logging.getLogger(__name__)


class RoleAdmin(admin.ModelAdmin):
    form = RoleAdminForm
    filter_horizontal = ['permissions']

    fieldsets = (
        (None, {'fields': ('name', )},),
        (_("Permissions"), {'fields': ('permissions', )},),
        (_("Users"), {'fields': ('users', )},),
    )

    def queryset(self, request):
        return self.model.objects.filter(name__startswith="role")
