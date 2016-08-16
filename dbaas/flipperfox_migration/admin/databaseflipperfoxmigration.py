# -*- coding: utf-8 -*-
import logging
from django_services import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.conf.urls import url, patterns
from django.http import HttpResponseRedirect
from dateutil import tz
from notification.models import TaskHistory
from ..models import DatabaseFlipperFoxMigration
from ..models import DatabaseFlipperFoxMigrationDetail
from ..service.databaseflipperfoxmigration import DatabaseFlipperFoxMigrationService
from ..tasks import execute_database_flipperfox_migration
from ..tasks import execute_database_flipperfox_migration_undo
from django.shortcuts import render_to_response
from django.template import RequestContext
from ..forms import DatabaseFlipperFoxMigrationDetailForm

LOG = logging.getLogger(__name__)


class DatabaseFlipperFoxMigrationAdmin(admin.DjangoServicesAdmin):
    search_fields = ("database__name", "database__team__name",
                     "database__databaseinfra__name",
                     "database__project__name")

    list_filter = ["database__project", "database__team"]

    list_display = ('database', 'steps_information', 'database_engine',
                    'get_database_team', 'status', 'description',
                    'schedule_next_step_html', 'user_friendly_warning',
                    'schedule_rollback_html',)

    model = DatabaseFlipperFoxMigration
    actions = None
    service_class = DatabaseFlipperFoxMigrationService
    list_display_links = ()
    template = 'flipperfox_migration/databaseflipperfoxmigration/schedule_next_step.html'

    def __init__(self, *args, **kwargs):
        super(DatabaseFlipperFoxMigrationAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def get_step_id(self, databaseflipperfoxmigration,):
        id = databaseflipperfoxmigration.id
        current_step = databaseflipperfoxmigration.current_step
        last_step = len(databaseflipperfoxmigration.get_steps()) - 1

        is_migration_finished = current_step == last_step

        waiting_status = DatabaseFlipperFoxMigrationDetail.WAITING
        running_status = DatabaseFlipperFoxMigrationDetail.RUNNING

        migration_running_or_waiting = DatabaseFlipperFoxMigrationDetail.objects.\
            filter(database_flipperfox_migration=databaseflipperfoxmigration,
                   status__in=[waiting_status, running_status])

        if is_migration_finished or migration_running_or_waiting:
            return ''

        return id

    def schedule_next_step_html(self, databaseflipperfoxmigration):
        id = self.get_step_id(databaseflipperfoxmigration)
        html = ''

        if id:
            html = "<a class='btn btn-info' href='{}/schedulenextstep/'><i\
                    class='icon-chevron-right icon-white'></i></a>".format(id)

        return format_html(html)

    schedule_next_step_html.short_description = "Schedule Next Macro Step"

    def schedule_rollback_html(self, databaseflipperfoxmigration):
        id = self.get_step_id(databaseflipperfoxmigration)
        html = ''

        if id and databaseflipperfoxmigration.current_step > 0:
            html = "<a class='btn btn-info' href='{}/schedulenextstep/?rollback=true'><i\
                    class='icon-chevron-left icon-white'></i></a>".format(id)

        return format_html(html)

    schedule_rollback_html.short_description = "Schedule Rollback"

    def database_engine(self, databaseflipperfoxmigration):
        return databaseflipperfoxmigration.database.engine_type

    database_engine.short_description = "Engine"

    def user_friendly_warning(self, databaseflipperfoxmigration):
        warning_message = databaseflipperfoxmigration.warning

        if warning_message:
            html = '<span class="label label-warning"><font size=3.5>\
                    {}</font></span>'.format(warning_message)
            return format_html(html)

        return warning_message

    user_friendly_warning.short_description = "Warning"

    def get_database_team(self, databaseflipperfoxmigration):
        return databaseflipperfoxmigration.database.team

    get_database_team.short_description = "Team"

    def steps_information(self, databaseflipperfoxmigration):
        current_step = databaseflipperfoxmigration.current_step + 1
        steps_len = str(len(databaseflipperfoxmigration.get_steps()) - 1)
        html = "<a href='../databaseflipperfoxmigrationdetail/?database_flipperfox_migration={}'>{}</a>"
        information = '{} of {}'.format(current_step, steps_len)

        if current_step > int(steps_len):
            html = '<center>-</center>'
        else:
            html = html.format(databaseflipperfoxmigration.id, information)

        return format_html(html)

    steps_information.short_description = "Current Macro Step"

    def get_urls(self):
        urls = super(DatabaseFlipperFoxMigrationAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^/?(?P<databaseflipperfoxmigration_id>\d+)/schedulenextstep/$',
                               self.admin_site.admin_view(self.databaseflipperfoxmigration_view)),
                           )
        return my_urls + urls

    def databaseflipperfoxmigration_view(self, request, databaseflipperfoxmigration_id):
        form = DatabaseFlipperFoxMigrationDetailForm
        database_flipperfox_migration = DatabaseFlipperFoxMigration.objects.get(
            id=databaseflipperfoxmigration_id)

        if request.method == 'POST':
            form = DatabaseFlipperFoxMigrationDetailForm(request.POST)
            if form.is_valid():
                scheduled_for = form.cleaned_data['scheduled_for']

                database_flipperfox_migration_detail = DatabaseFlipperFoxMigrationDetail(
                    database_flipperfox_migration=database_flipperfox_migration,
                    step=database_flipperfox_migration.current_step,
                    scheduled_for=scheduled_for,
                    created_by=request.user.username)

                database_flipperfox_migration_detail.save()

                task_history = TaskHistory()
                task_history.task_name = "execute_database_flipperfox_migration"
                task_history.task_status = task_history.STATUS_WAITING

                description = database_flipperfox_migration.description()
                task_history.arguments = "Database name: {},\
                                          Macro step: {}".format(database_flipperfox_migration.database.name,
                                                                 description)
                task_history.user = request.user
                task_history.save()

                is_rollback = request.GET.get('rollback')
                scheduled_for.replace(
                    tzinfo=tz.tzlocal()).astimezone(tz.tzutc())

                if is_rollback:
                    LOG.info("Rollback!")
                    database_flipperfox_migration_detail.step -= 1
                    database_flipperfox_migration_detail.save()
                    task = execute_database_flipperfox_migration_undo.apply_async(
                        args=[database_flipperfox_migration_detail.id,
                              task_history,
                              request.user],
                        eta=scheduled_for)
                else:
                    task = execute_database_flipperfox_migration.apply_async(
                        args=[database_flipperfox_migration_detail.id,
                              task_history, request.user],
                        eta=scheduled_for)

                database_flipperfox_migration_detail.celery_task_id = task.task_id
                database_flipperfox_migration_detail.save()

                url = reverse('admin:notification_taskhistory_changelist')
                return HttpResponseRedirect(url + "?user=%s" % request.user.username)

        return render_to_response("flipperfox_migration/databaseflipperfoxmigrationdetail/schedule_next_step.html",
                                  locals(),
                                  context_instance=RequestContext(request))
