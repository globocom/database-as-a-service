# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from account.models import Role, Team


from util import email_notifications

LOG = logging.getLogger(__name__)


class RoleListFilter(SimpleListFilter):
    title = _('roles')

    parameter_name = 'role'

    def lookups(self, request, model_admin):
        qs = Role.objects.all()
        return [(i.id, i.name) for i in qs]

    def queryset(self, request, queryset):
        users = []
        if self.value():
            teams = Team.objects.filter(role=self.value())
            for team in teams:
                for user in team.users.all():
                    users.append(user.id)
            return queryset.filter(id__in=users)


class UserTeamListFilter(SimpleListFilter):
    title = _('team')

    parameter_name = 'team'

    def lookups(self, request, model_admin):
        qs = Team.objects.filter(users=request.user)
        return [(i.id, i.name) for i in qs]


class TeamListFilter(SimpleListFilter):
    title = _('team')

    parameter_name = 'team'

    def lookups(self, request, model_admin):
        qs = Team.objects.all()
        return [(-1, _("without team"))] + [(i.id, i.name) for i in qs]

    def queryset(self, request, queryset):
        users = []
        if self.value():
            if self.value() == '-1':
                users_id = []
                teams = Team.objects.all()
                for team in teams:
                    for user in team.users.all():
                        if user.id not in users_id:
                            users_id.append(user.id)

                return queryset.exclude(id__in=users_id)
            else:
                teams = Team.objects.filter(id=self.value())
                for team in teams:
                    for user in team.users.all():
                        users.append(user.id)
                return queryset.filter(id__in=users)


class UserAdmin(UserAdmin):

    list_display = ('username', 'email', 'get_team_for_user')
    list_filter = ('is_active', RoleListFilter, TeamListFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    fieldsets_basic = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
         'fields': ('first_name', 'last_name', 'email', 'is_active', 'is_staff')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    fieldsets_advanced = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser')}),
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
                # return super(UserAdmin, self).get_fieldsets(request, obj=obj)
                return self.fieldsets_advanced
            else:
                return self.fieldsets_basic

    def get_readonly_fields(self, request, obj=None):
        """
        if user is not superuser, than is_staff field should be readonly
        """

        if obj:  # In edit mode
            if request.user.is_superuser:
                return ()
            else:
                return ('is_staff',)
        else:
            return ()

    def save_related(self, request, form, formsets, change):
        """overrides save_related to send an email if the user team changes"""

        instance = form.instance

        teams_before_save = [team.id for team in instance.team_set.all()]
        LOG.debug("teams for user %s before save: %s" %
                  (instance, teams_before_save))
        super(UserAdmin, self).save_related(request, form, formsets, change)
        teams_after_save = [team.id for team in instance.team_set.all()]
        LOG.debug("teams for user %s after save: %s" %
                  (instance, teams_after_save))

        if cmp(teams_before_save, teams_after_save):
            email_notifications.notify_team_change_for(user=instance)
