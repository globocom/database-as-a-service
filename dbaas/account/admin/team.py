# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging
from ..forms.team import TeamAdminForm


LOG = logging.getLogger(__name__)


class TeamAdmin(admin.ModelAdmin):

    list_display = ["name", "role"]
    filter_horizontal = ['users']
    
    form = TeamAdminForm
    # #filter_horizontal = ['permissions']
    # 
    # fieldsets = (
    #     (None, {'fields': ('name', )},),
    #     (_("Users"), {'fields': ('users', )},),
    # )
    # 
    # def queryset(self, request):
    #     return self.model.objects.exclude(name__startswith="role")
