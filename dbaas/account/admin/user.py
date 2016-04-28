# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import logging
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import SimpleListFilter
from account.models import Role, Team
from ..forms.user import CustomUserChangeForm, CustomUserCreationForm
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.conf import settings
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.core.exceptions import ValidationError

from util import email_notifications

LOG = logging.getLogger(__name__)

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())


def validate_user_length(value):
    username_length = len(value)
    if username_length > 100:
        return ValidationError(
            'Ensure this value has at most 100 characters (it has {}).'.format(username_length)
        )


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


class CustomUserAdmin(UserAdmin):

    list_display = ('username', 'email', 'get_team_for_user')
    list_filter = ('is_active', RoleListFilter, TeamListFilter,)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

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

    @sensitive_post_parameters_m
    @csrf_protect_m
    @transaction.atomic
    def add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    'order to add users, Django requires that your user '
                    'account have both the "Add user" and "Change user" '
                    'permissions set.')
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        username_field = self.model._meta.get_field(self.model.USERNAME_FIELD)
        username_field.max_length = 100
        username_field.help_text = "Required. 100 characters or fewer. Letters, digits and @/./+/-/_ only."
        username_field.validators[1] = validate_user_length
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': username_field.help_text,
        }
        extra_context.update(defaults)
        return super(CustomUserAdmin, self).add_view(
            request, form_url, extra_context)
