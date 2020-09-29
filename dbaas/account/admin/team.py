# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from account.templatetags import team as team_templatetag
import logging

from ..models import Role

LOG = logging.getLogger(__name__)


class RoleListFilter(SimpleListFilter):
    title = _('roles')

    parameter_name = 'role'

    def lookups(self, request, model_admin):
        qs = Role.objects.all()
        return [(-1, _("without role"))] + [(i.id, i.name) for i in qs]

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '-1':
                return queryset.exclude(
                    role_id__in=[role.id for role in Role.objects.all()]
                )
            else:
                return queryset.filter(role_id=self.value())


class TeamAdmin(admin.ModelAdmin):

    list_display = ["name", "role", "database_limit", "email", "organization"]
    filter_horizontal = ['users']
    list_filter = (RoleListFilter, "organization", )
    search_fields = ('name',)
    readonly_fields = ["token", ]

    def database_limit(self, team):
        return team_templatetag.render_usage(team)
