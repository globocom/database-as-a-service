# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging


LOG = logging.getLogger(__name__)


class TeamAdmin(admin.ModelAdmin):

    filter_horizontal = ['permissions']

    def has_add_permission(self, request):
        if not request.user.is_active:
            return False
        else:
            return request.user.has_perm("auth.add_group", obj=None)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_active:
            return False
        else:
            return request.user.has_perm("auth.change_group", obj=None)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_active:
            return False
        else:
            return request.user.has_perm("auth.delete_group", obj=None)

    def queryset(self, request):
        return self.model.objects.exclude(name__startswith="role")
