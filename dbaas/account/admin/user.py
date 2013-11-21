# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging
from django.contrib.auth.admin import UserAdmin

from account.models import Team

LOG = logging.getLogger(__name__)

class TeamInline(admin.StackedInline):
    model = Team.users.through
    can_delete = False
    extra = 1
    max_num = 1
    verbose_name = _("Team")
    verbose_name_plural = _("Teams")


class UserAdmin(UserAdmin):
    
    inlines = (TeamInline, )
    
    fieldsets_basic = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_active')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    fieldsets_advanced = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        else:
            if request.user.is_superuser:
                #return super(UserAdmin, self).get_fieldsets(request, obj=obj)
                return self.fieldsets_advanced
            else:
                return self.fieldsets_basic
