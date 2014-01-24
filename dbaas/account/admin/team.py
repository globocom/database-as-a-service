# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, escape
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
import logging

from ..forms.team import TeamAdminForm
from ..models import Role
from logical.models import Environment

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
                return queryset.exclude(role_id__in=[role.id for role in Role.objects.all()])
            else:
                return queryset.filter(role_id=self.value())

class TeamAdmin(admin.ModelAdmin):

    list_display = ["name", "role", "database_limit", "email"]
    filter_horizontal = ['users']
    list_filter = (RoleListFilter, )
    search_fields = ('name',)
    #form = TeamAdminForm

    def database_limit(self, team):
        environments = Environment.objects.all()
        html = []
        html.append("<ul>")
        for environment in environments:
            html.append("<li>%s: %s of %s in use</li>" % (environment, 
                                                            team.count_databases_in_use(environment),
                                                            team.database_alocation_limit))

        return format_html("".join(html))
        #return team.database_alocation_limit
