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
from django.contrib.admin import helpers
from django.forms.formsets import all_valid
from django.utils.encoding import force_text
from django.core.urlresolvers import reverse
from django.contrib.admin.util import unquote
from util import email_notifications
from django.utils.html import escape

LOG = logging.getLogger(__name__)

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

IS_POPUP_VAR = '_popup'


def validate_user_length(value):
    username_length = len(value)
    if username_length > 100:
        return ValidationError(
            'Ensure this value has at most 100 characters (it has {}).'.format(
                username_length)
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

    def _get_users(self, teams):
        users = []
        for team in teams:
            for user in team.users.all():
                if user.id not in users:
                    users.append(user.id)
        return users

    def queryset(self, request, queryset):
        if self.value() == '-1':
            return queryset.exclude(id__in=self._get_users(Team.objects.all()))
        elif self.value():
            return queryset.filter(
                id__in=self._get_users(Team.objects.filter(id=self.value()))
            )
        return queryset


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
        username_field.help_text = ("Required. 100 characters or fewer. "
                                    "Letters, digits and @/./+/-/_ only.")
        username_field.validators[1] = validate_user_length
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': username_field.help_text,
        }
        extra_context.update(defaults)
        return super(CustomUserAdmin, self).add_view(
            request, form_url, extra_context)

    # @csrf_protect_m
    # @transaction.atomic
    # def change_view(self, request, form_url='', extra_context=None):
        username_field = self.model._meta.get_field(self.model.USERNAME_FIELD)
        username_field.max_length = 100
        username_field.help_text = ("Required. 100 characters or fewer. "
                                    "Letters, digits and @/./+/-/_ only.")
        username_field.validators[1] = validate_user_length

    @csrf_protect_m
    @transaction.atomic
    def change_view(self, request, object_id, form_url='', extra_context=None):
        "The 'change' admin view for this model."
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(
                _(('%(name)s object with primary key %(key)r '
                   'does not exist.')) % {
                          'name': force_text(opts.verbose_name),
                          'key': escape(object_id)
                })

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(
                request,
                form_url=reverse(
                    'admin:%s_%s_add' % (
                        opts.app_label,
                        opts.model_name),
                    current_app=self.admin_site.name)
                )

        ModelForm = self.get_form(request, obj)
        formsets = []
        inline_instances = self.get_inline_instances(request, obj)
        if request.method == 'POST':
            username_field = self.model._meta.get_field(
                self.model.USERNAME_FIELD
            )
            username_field.max_length = 100
            username_field.help_text = ("Required. 100 characters or fewer. "
                                        "Letters, digits and @/./+/-/_ only.")
            username_field.validators[1] = validate_user_length
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request, new_object),
                                       inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix,
                                  queryset=inline.get_queryset(request))

                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, True)
                self.save_related(request, form, formsets, True)
                change_message = self.construct_change_message(
                    request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request, obj),
                                       inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix,
                                  queryset=inline.get_queryset(request))
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
                                      self.get_prepopulated_fields(
                                          request, obj),
                                      self.get_readonly_fields(request, obj),
                                      model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(
                inline, formset,
                fieldsets, prepopulated, readonly, model_admin=self
            )
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change %s') % force_text(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': IS_POPUP_VAR in request.REQUEST,
            'media': media,
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
            'preserved_filters': self.get_preserved_filters(request),
        }
        context.update(extra_context or {})
        return self.render_change_form(
            request, context, change=True, obj=obj, form_url=form_url
        )
