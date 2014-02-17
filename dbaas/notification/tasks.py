# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings

from system.models import Configuration
from celery.utils.log import get_task_logger
from celery.exceptions import SoftTimeLimitExceeded
from dbaas.celery import app

from util import call_script
from util.decorators import only_one
from util import email_notifications
from .util import get_clone_args
from .models import TaskHistory
from drivers import factory_for
from django.db.models import Sum, Count

from physical.models import DatabaseInfra
from account.models import Team

LOG = get_task_logger(__name__)

def get_history_for_task_id(task_id):
    try:
        return TaskHistory.objects.get(task_id=task_id)
    except Exception, e:
        LOG.error("could not find history for task id %s" % task_id)
        return None


def rollback_database(dest_database):
    dest_database.is_in_quarantine = True
    dest_database.save()
    dest_database.delete()


@app.task(bind=True)
def clone_database(self, origin_database, dest_database, user=None):
    
    #register History
    task_history = TaskHistory.register(request=self.request, user=user)
    
    LOG.info("origin_database: %s" % origin_database)
    LOG.info("dest_database: %s" % dest_database)
    # task_state = self.AsyncResult(self.request.id).state)
    LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (self.request.id,
                                                            self.request.task,
                                                            self.request.kwargs,
                                                            str(self.request.args)))

    args = get_clone_args(origin_database, dest_database)

    try:
        script_name = factory_for(origin_database.databaseinfra).clone()
        #script_name = "dummy_clone.sh"
        return_code, output = call_script(script_name, working_dir=settings.SCRIPTS_PATH, args=args)
        LOG.info("%s - return code: %s" % (self.request.id, return_code))
        if return_code != 0:
            task_history.update_status_for(TaskHistory.STATUS_ERROR, details=output)
            LOG.error("task id %s - error occurred. Transaction rollback" % self.request.id)
            rollback_database(dest_database)
        else:
            task_history.update_status_for(TaskHistory.STATUS_SUCCESS)
    except SoftTimeLimitExceeded:
        LOG.error("task id %s - timeout exceeded" % self.request.id)
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details="timeout exceeded")
    except Exception, e:
        LOG.error("task id %s error: %s" % (self.request.id, e))
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)
    return

@app.task
@only_one(key="db_infra_notification_key", timeout=20)
def databaseinfra_notification():
    # Sum capacity per databseinfra with parameter plan, environment and engine
    infras = DatabaseInfra.objects.values('plan__name', 'environment__name', 'engine__engine_type__name').annotate(capacity=Sum('capacity'))
    for infra in infras:
        # total database created in databaseinfra per plan, environment and engine
        used = DatabaseInfra.objects.filter(plan__name=infra['plan__name'], environment__name=infra['environment__name'], engine__engine_type__name=infra['engine__engine_type__name']).aggregate(used=Count('databases'))
        # calculate the percentage
        percent = int(used['used'] * 100 / infra['capacity'])
        if percent >= Configuration.get_by_name_as_int("threshold_infra_notification", default=50):
            LOG.info('Plan %s in environment %s with %s%% occupied' % (infra['plan__name'], infra['environment__name'],percent))
            LOG.info("Sending database infra notification...")
            context={}
            context['plan'] = infra['plan__name']
            context['environment'] = infra['environment__name']
            context['used'] = used['used']
            context['capacity'] = infra['capacity']
            context['percent'] = percent
            email_notifications.databaseinfra_ending(context=context)
    return

@app.task(bind=True)
@only_one(key="db_notification_for_team_key", timeout=20)
def database_notification_for_team(self, team=None):
    """
    Notifies teams of database usage.
    if threshold_database_notification <= 0, the notification is disabled.
    """
    from logical.models import Database
    LOG.info("sending database notification for team %s" % team)
    threshold_database_notification = Configuration.get_by_name_as_int("threshold_database_notification", default=50)
    #if threshold_database_notification 
    if threshold_database_notification <= 0:
        LOG.warning("database notification is disabled")
        return

    databases = Database.objects.filter(team=team)
    msgs = []
    for database in databases:
        used = database.used_size_in_mb
        capacity = database.total_size_in_mb
        try:
            percent_usage = (used / capacity) * 100
        except ZeroDivisionError:
            #database has no total size
            percent_usage = 0.0
        msg = "database %s => usage: %.2f | threshold: %.2f" % (database, percent_usage, threshold_database_notification)
        LOG.info(msg)
        msgs.append(msg)

        if percent_usage >= threshold_database_notification:
            LOG.info("Sending database notification...")
            context = {}
            context['database'] = database.name
            context['team'] = team
            context['measure_unity'] = "MB"
            context['used'] = used
            context['capacity'] = capacity
            context['percent'] = "%.2f" % percent_usage
            context['environment'] = database.environment.name
            email_notifications.database_usage(context=context)

    if team.email:
        task_history = TaskHistory.register(request=self.request, user=None)
        task_history.update_status_for(TaskHistory.STATUS_SUCCESS, details="\n".join(msgs))
    else:
        msg = "team %s has no email set and therefore no database usage notification will been sent" % team
        LOG.error(msg)
        #register History
        task_history = TaskHistory.register(request=self.request, user=None)
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=msg)

    return

@app.task(bind=True)
@only_one(key="db_notification_key", timeout=20)
def database_notification(self):
    """
    Create tasks for database notification by team
    if threshold_database_notification <= 0, the notification is disabled.
    """
    #get all teams and for each one create a new task
    LOG.info("retrieving all teams and sendind database notification")
    teams = Team.objects.all()
    for team in teams:
        ###############################################
        # create task
        ###############################################
        result = database_notification_for_team.delay(team=team)
        ###############################################

    return
