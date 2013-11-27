# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
import logging
from django.utils.html import format_html, escape
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
    
    list_display = ('username', 'email', 'get_team_for_user')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets_basic = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_active', 'is_staff')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    fieldsets_advanced = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_team_for_user(self, user):
        teams = user.team_set.all()
        team_html = []
        if teams:
            team_html.append("<ul>")
            for team in teams:
                team_html.append("<li>%s</li>" % team.name)
            team_html.append("</ul>")
            return format_html("".join(team_html))
        else:
            return "N/A"

    
    get_team_for_user.short_description = "Team(s)"

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        else:
            if request.user.is_superuser:
                #return super(UserAdmin, self).get_fieldsets(request, obj=obj)
                return self.fieldsets_advanced
            else:
                return self.fieldsets_basic

    def get_readonly_fields(self, request, obj=None):
        """
        if user is not superuser, than is_staff field should be readonly
        """
        if obj: #In edit mode
            if request.user.is_superuser:
                return ()
            else:
                return ('is_staff',)
        else:
            return ()

