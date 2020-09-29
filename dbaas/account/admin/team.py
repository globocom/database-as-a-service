# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.contrib.admin import SimpleListFilter, helpers
from account.templatetags import team as team_templatetag
import logging
from django.core.exceptions import PermissionDenied
from django.contrib.admin.options import csrf_protect_m, \
    IncorrectLookupParameters
from django.contrib.auth import get_permission_codename
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.http import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ungettext

from account.models import Role
from account.forms.team import TeamAdminForm
from account.service.team import TeamService

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


class TeamAdmin(admin.DjangoServicesAdmin):

    form = TeamAdminForm
    service_class = TeamService
    list_display = ["name", "role", "database_limit", "email", "organization"]
    filter_horizontal = ['users']
    list_filter = (RoleListFilter, "organization")
    search_fields = ('name',)
    readonly_fields = ["token", ]

    def database_limit(self, team):
        return team_templatetag.render_usage(team)

    def get_actions(self, request):
        actions = super(TeamAdmin, self).get_actions(request)
        if not self.has_change_permission(request, None):
            del actions['delete_selected']
        return actions

    def has_view_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('view', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def get_model_perms(self, request):
        return {
            'add': self.has_add_permission(request),
            'change': self.has_change_permission(request),
            'delete': self.has_delete_permission(request),
            'view': self.has_view_permission(request),
        }

    def queryset(self, request):
        is_dba = request.user.team_set.filter(role__name="role_dba").exists()
        if is_dba:
            return super(TeamAdmin, self).queryset(request)
        else:
            return request.user.team_set.all()

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        """
        The 'change list' admin view for this model.
        """
        from django.contrib.admin.views.main import ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_view_permission(request, None) and not self.has_change_permission(request, None):
            raise PermissionDenied

        list_display = self.get_list_display(request)
        if self.has_change_permission(request, None):
            list_display_links = self.get_list_display_links(
                request, list_display
            )
        else:
            list_display_links = (None,)
        list_filter = self.get_list_filter(request)

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        if actions:
            # Add the action checkboxes if there are any actions available.
            list_display = ['action_checkbox'] + list(list_display)

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, list_display,
                            list_display_links, list_filter,
                            self.date_hierarchy, self.search_fields,
                            self.list_select_related, self.list_per_page,
                            self.list_max_show_all, self.list_editable, self)
        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.
        action_failed = False
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)

        # Actions with no confirmation
        if (actions and request.method == 'POST' and
                'index' in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(
                    request, queryset=cl.get_queryset(request)
                )
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                self.message_user(request, msg, messages.WARNING)
                action_failed = True

        # Actions with confirmation
        if (actions and request.method == 'POST' and
                helpers.ACTION_CHECKBOX_NAME in request.POST and
                'index' not in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(
                    request, queryset=cl.get_queryset(request)
                )
                if response:
                    return response
                else:
                    action_failed = True

        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        formset = cl.formset = None

        # Handle POSTed bulk-edit data.
        if (request.method == "POST" and cl.list_editable and
                '_save' in request.POST and not action_failed):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(
                request.POST, request.FILES, queryset=cl.result_list
            )
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(
                            request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        self.save_related(
                            request, form, formsets=[], change=True
                        )
                        change_msg = self.construct_change_message(
                            request, form, None
                        )
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    if changecount == 1:
                        name = force_text(opts.verbose_name)
                    else:
                        name = force_text(opts.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_text(obj)}
                    self.message_user(request, msg, messages.SUCCESS)

                return HttpResponseRedirect(request.get_full_path())

        # Handle GET -- construct a formset for display.
        elif cl.list_editable:
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        # Build the list of media to be used by the formset.
        if formset:
            media = self.media + formset.media
        else:
            media = self.media

        # Build the action form and populate it with available actions.
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None

        selection_note_all = ungettext('%(total_count)s selected',
                                       'All %(total_count)s selected',
                                       cl.result_count)


        context = {
            'module_name': force_text(opts.verbose_name_plural),
            'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            'selection_note_all': selection_note_all % {'total_count': cl.result_count},
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'media': media,
            'has_add_permission': self.has_add_permission(request),
            'opts': cl.opts,
            'app_label': app_label,
            'action_form': action_form,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': self.actions_selection_counter,
            'preserved_filters': self.get_preserved_filters(request),
        }
        context.update(extra_context or {})

        return TemplateResponse(request, self.change_list_template or [
            'admin/%s/%s/change_list.html' % (app_label, opts.model_name),
            'admin/%s/change_list.html' % app_label,
            'admin/change_list.html'
        ], context, current_app=self.admin_site.name)
