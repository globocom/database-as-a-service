# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import date, timedelta, datetime
import traceback

from celery.utils.log import get_task_logger
from django.db.models import Sum, Count, Q
from simple_audit.models import AuditRequest
from django.db.models.signals import post_save


from account.models import User
from dbaas.celery import app
from account.models import Team
from logical.models import Database
from physical.models import Plan, DatabaseInfra, Instance
from util import email_notifications, get_worker_name
from util.decorators import only_one
from util import providers as util_providers
from system.models import Configuration
from notification.models import TaskHistory
from workflow.workflow import (steps_for_instances,
                               rollback_for_instances_full,
                               total_of_steps)
from maintenance import models as maintenance_models
from maintenance import tasks as maintenace_tasks
from maintenance.models import DatabaseDestroy
from util import slugify, gen_infra_names
from maintenance.tasks_create_database import (get_or_create_infra,
                                               get_instances_for)


LOG = get_task_logger(__name__)


def get_history_for_task_id(task_id):
    try:
        return TaskHistory.objects.get(task_id=task_id)
    except Exception:
        LOG.error("could not find history for task id %s" % task_id)
        return None


def rollback_database(dest_database):
    dest_database.is_in_quarantine = True
    dest_database.save()
    dest_database.delete()


def create_database_with_retry(
    name, plan, environment, team, project, description,
    task, backup_hour, maintenance_window, maintenance_day,
    subscribe_to_email_events, is_protected, user, retry_from
):
    from maintenance.tasks import create_database
    return create_database.delay(
        name=name, plan=plan, environment=environment, team=team,
        project=project, description=description, task=task,
        backup_hour=backup_hour, maintenance_window=maintenance_window,
        maintenance_day=maintenance_day,
        subscribe_to_email_events=subscribe_to_email_events,
        is_protected=is_protected, user=user, retry_from=retry_from
    )


@app.task(bind=True)
def destroy_database(self, database, task_history=None, user=None):
    # register History
    AuditRequest.new_request("destroy_database", user, "localhost")
    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, task_history=task_history,
            user=user, worker_name=worker_name
        )

        LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
            self.request.id, self.request.task,
            self.request.kwargs, str(self.request.args))
        )

        task_history.add_detail('Quarantine:')
        task_history.add_detail(
            'Since: {}'.format(database.quarantine_dt), level=2
        )
        task_history.add_detail(
            'Requested by: {}'.format(database.quarantine_user), level=2
        )
        task_history.add_detail('')
        task_history.add_detail('Loading Process...')

        infra = database.databaseinfra

        database_destroy = DatabaseDestroy()
        database_destroy.task = task_history
        database_destroy.name = database.name
        database_destroy.plan = database.plan
        database_destroy.environment = database.environment
        database_destroy.team = database.team
        database_destroy.project = database.project
        database_destroy.description = database.description
        database_destroy.is_protected = database.is_protected
        database_destroy.user = user.username if user else task_history.user
        database_destroy.infra = database.infra
        database_destroy.database = infra.databases.first()
        database_destroy.save()

        topology_path = database_destroy.plan.replication_topology.class_path
        steps = util_providers.get_deploy_settings(topology_path)

        instances = ([host.instances.order_by('instance_type').first()
                     for host in infra.hosts])
        database_destroy.current_step = total_of_steps(steps, instances)

        database_destroy.save()

        from maintenance.tasks_create_database import rollback_create
        rollback_create(database_destroy, task_history, user,
                        instances=instances)
        if task_history.task_status == TaskHistory.STATUS_ERROR:
            return
        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS,
            details='Database destroyed successfully')
        return
    finally:
        AuditRequest.cleanup_request()


@app.task(bind=True)
def destroy_database_retry(self, rollback_from, task, user):
    from maintenance.tasks import _create_database_rollback
    _create_database_rollback(self, rollback_from, task, user)


@app.task(bind=True)
def clone_database(self, origin_database, clone_name, plan, environment,
                   task_history=None, user=None, retry_from=None):
    AuditRequest.new_request("clone_database", user, "localhost")
    worker_name = get_worker_name()
    LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
        self.request.id, self.request.task,
        self.request.kwargs, str(self.request.args))
    )

    task = TaskHistory.register(
        request=self.request, task_history=task_history,
        user=user, worker_name=worker_name
    )

    LOG.info("origin_database: %s" % origin_database)

    topology_path = plan.replication_topology.class_path

    name = slugify(clone_name)
    base_name = gen_infra_names(name, 0)
    infra = get_or_create_infra(
        base_name, plan, environment, retry_from=retry_from
    )
    instances = get_instances_for(infra, topology_path)

    step_manager = maintenance_models.DatabaseClone()
    step_manager.task = task
    step_manager.name = name
    step_manager.plan = plan
    step_manager.environment = environment
    step_manager.user = user.username if user else task.user
    step_manager.infra = infra
    step_manager.database = infra.databases.first()
    step_manager.origin_database = origin_database
    step_manager.save()

    steps = util_providers.get_clone_settings(topology_path)

    since_step = None
    if retry_from:
        since_step = retry_from.current_step

    if steps_for_instances(
        steps, instances, task, step_manager.update_step,
        since_step=since_step, step_manager=step_manager
    ):
        step_manager.set_success()
        task.set_status_success('Database cloned')
        step_manager.database.finish_task()
    else:
        step_manager.set_error()
        task.set_status_error(
            'Could not create database\n'
            'Please check error message and do retry'
        )
    AuditRequest.cleanup_request()


@app.task(bind=True)
def clone_database_rollback(self, rollback_from, task, user, instances=None):
    task = TaskHistory.register(
        request=self.request, task_history=task, user=user,
        worker_name=get_worker_name()
    )
    topology_path = rollback_from.plan.replication_topology.class_path
    steps = util_providers.get_clone_settings(topology_path)

    if instances is None:
        instances = get_instances_for(rollback_from.infra, topology_path)

    rollback_from.id = None
    rollback_from.user = user.username if user else task.user
    rollback_from.task = task
    rollback_from.save()

    if rollback_for_instances_full(
        steps, instances, task, rollback_from.get_current_step,
        rollback_from.update_step, step_manager=rollback_from
    ):
        rollback_from.set_rollback()
        task.set_status_success('Rollback executed with success')

        infra = rollback_from.infra
        infra.delete()
    else:
        rollback_from.set_error()
        task.set_status_error(
            'Could not do rollback\n'
            'Please check error message and do retry'
        )


@app.task
@only_one(key="db_infra_notification_key", timeout=20)
def databaseinfra_notification(self, user=None):
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, user=user, worker_name=worker_name)
    threshold_infra_notification = Configuration.get_by_name_as_int(
        "threshold_infra_notification", default=0)
    if threshold_infra_notification <= 0:
        LOG.warning("database infra notification is disabled")
        return

    # Sum capacity per databseinfra with parameter plan, environment and engine
    infras = DatabaseInfra.objects.values(
        'plan__name', 'environment__name', 'engine__engine_type__name',
        'plan__provider'
    ).annotate(capacity=Sum('capacity'))
    for infra in infras:
        try:
            database = infra.databases.get()
        except Database.MultipleObjectsReturned:
            pass
        else:
            if database.is_in_quarantine:
                continue
            if not database.subscribe_to_email_events:
                continue

        used = DatabaseInfra.objects.filter(
            plan__name=infra['plan__name'],
            environment__name=infra['environment__name'],
            engine__engine_type__name=infra['engine__engine_type__name']
        ).aggregate(used=Count('databases'))
        # calculate the percentage

        percent = int(used['used'] * 100 / infra['capacity'])
        if (percent >= threshold_infra_notification
                and infra['plan__provider'] != Plan.CLOUDSTACK):
            LOG.info('Plan %s in environment %s with %s%% occupied' % (
                infra['plan__name'], infra['environment__name'], percent))
            LOG.info("Sending database infra notification...")
            context = {}
            context['plan'] = infra['plan__name']
            context['environment'] = infra['environment__name']
            context['used'] = used['used']
            context['capacity'] = infra['capacity']
            context['percent'] = percent
            email_notifications.databaseinfra_ending(context=context)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS,
            details=('Databaseinfra Notification successfully sent to '
                     'dbaas admins!')
        )
    return


def database_notification_for_team(team=None):
    """
    Notifies teams of database usage.
    if threshold_database_notification <= 0, the notification is disabled.
    """
    LOG.info("sending database notification for team %s" % team)
    threshold_database_notification = Configuration.get_by_name_as_int(
        "threshold_database_notification", default=0)
    # if threshold_database_notification
    if threshold_database_notification <= 0:
        LOG.warning("database notification is disabled")
        return

    databases = Database.objects.filter(
        team=team, is_in_quarantine=False, subscribe_to_email_events=True
    )
    msgs = []
    for database in databases:
        used = database.used_size_in_mb
        capacity = database.total_size_in_mb
        try:
            percent_usage = (used / capacity) * 100
        except ZeroDivisionError:
            # database has no total size
            percent_usage = 0.0
        msg = "database %s => usage: %.2f | threshold: %.2f" % (
            database, percent_usage, threshold_database_notification)
        LOG.info(msg)
        msgs.append(msg)

        if not team.email:
            msgs.append(
                ("team %s has no email set and therefore no database "
                 "usage notification will been sent") % team)
        else:
            if percent_usage >= threshold_database_notification:
                LOG.info("Sending database notification...")
                context = {}
                context['database'] = database
                context['team'] = team
                context['measure_unity'] = "MB"
                context['used'] = used
                context['capacity'] = capacity
                context['percent'] = "%.2f" % percent_usage
                context['environment'] = database.environment.name
                email_notifications.database_usage(context=context)

    return msgs


@app.task(bind=True)
@only_one(key="db_notification_key", timeout=180)
def database_notification(self):
    """
    Create tasks for database notification by team
    if threshold_database_notification <= 0, the notification is disabled.
    """
    # get all teams and for each one create a new task
    LOG.info("retrieving all teams and sending database notification")
    teams = Team.objects.all()
    msgs = {}

    for team in teams:
        ###############################################
        # create task
        ###############################################

        msgs[team] = database_notification_for_team(team=team)
        ###############################################

    try:
        LOG.info("Messages: ")
        LOG.info(msgs)

        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details="\n".join(
                (str(key) + ': ' + ', '.join(value)
                 for key, value in msgs.items())
            )
        )
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

    return


@app.task(bind=True)
@only_one(key="get_databases_status")
def update_database_status(self):
    LOG.info("Retrieving all databases")
    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        databases = Database.objects.all()
        msgs = []
        for database in databases:
            if database.database_status and database.database_status.is_alive:
                database.status = Database.ALIVE

                instances_status = (
                    database.databaseinfra.check_instances_status()
                )
                if instances_status == database.databaseinfra.ALERT:
                    database.status = Database.ALERT

            else:
                database.status = Database.DEAD

            database.save(update_fields=['status'])
            msg = "\nUpdating status for database: {}, status: {}".format(
                database, database.status)
            msgs.append(msg)
            LOG.info(msg)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details="\n".join(
                value for value in msgs
            )
        )
    except Exception:
        task_history.update_status_for(
            TaskHistory.STATUS_ERROR,
            details=traceback.format_exc()
        )

    return


@app.task(bind=True)
@only_one(key="get_databases_used_size")
def update_database_used_size_old(self):
    LOG.info("Retrieving all databases")
    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        databases = Database.objects.all()
        msgs = []
        for database in databases:
            if database.database_status:
                database.used_size_in_bytes = float(
                    database.database_status.used_size_in_bytes)
            else:
                database.used_size_in_bytes = 0.0

            database.save(update_fields=['used_size_in_bytes'])
            msg = ("\nUpdating used size in bytes for database: {}, used "
                   "size: {}").format(
                database, database.used_size_in_bytes)
            msgs.append(msg)
            LOG.info(msg)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details="\n".join(
                value for value in msgs
            )
        )
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

    return


@app.task(bind=True)
@only_one(key="update_infra_instances_sizes")
def update_infra_instances_sizes(self):
    """
        Update used and total size of all instances databases
    """

    LOG.info("Retrieving all databases")
    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        task_history.relevance = TaskHistory.RELEVANCE_WARNING
        databases = Database.objects.all()
        msgs = []
        for database in databases:
            updated_instances = database.driver.update_infra_instances_sizes()
            msg = ("\nUpdating used size in bytes for database: {}:\n\n"
                   "{}").format(database, "".join(updated_instances))
            msgs.append(msg)
            LOG.info(msg)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details="\n".join(
                value for value in msgs
            )
        )
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

    return


@app.task(bind=True)
@only_one(key="get_instances_status")
def update_instances_status(self):
    LOG.info("Retrieving all databaseinfras")
    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, user=None, worker_name=worker_name)
    task_history.relevance = TaskHistory.RELEVANCE_WARNING

    try:
        infras = DatabaseInfra.objects.all()
        msgs = []
        for databaseinfra in infras:
            LOG.info("Retrieving all instances for {}".format(databaseinfra))

            for instance in Instance.objects.filter(
                    databaseinfra=databaseinfra):
                instance.update_status()

                msg = ("\nUpdating instance status, instance: {}, "
                       "status: {}").format(
                    instance, instance.status)
                msgs.append(msg)
                LOG.info(msg)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details="\n".join(
                value for value in msgs
            )
        )
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)

    return


@app.task(bind=True)
@only_one(key="purge_task_history", timeout=600)
def purge_task_history(self):
    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, user=None, worker_name=worker_name)
        task_history.relevance = TaskHistory.RELEVANCE_WARNING

        now = datetime.now()
        retention_days = Configuration.get_by_name_as_int(
            'task_history_retention_days')

        n_days_before = now - timedelta(days=retention_days)

        tasks_to_purge = TaskHistory.objects.filter(
            task_name__in=[
                'notification.tasks.database_notification',
                'notification.tasks.database_notification_for_team',
                'notification.tasks.update_database_used_size',
                'notification.tasks.update_disk_used_size',
                'notification.tasks.update_database_status',
                'notification.tasks.update_instances_status',
                'notification.tasks.update_infra_instances_sizes',
                'sync_celery_tasks',
                'purge_unused_exports',
                'system.tasks.set_celery_healthcheck_last_update'
            ],
            ended_at__lt=n_days_before,
            task_status__in=["SUCCESS", "ERROR", "WARNING"])

        tasks_to_purge.delete()

        task_history.update_status_for(TaskHistory.STATUS_SUCCESS,
                                       details='Purge succesfully done!')
    except Exception as e:
        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=e)


@app.task(bind=True)
@only_one(key="sendmail24hoursbeforeautotask")
def send_mail_24hours_before_auto_task(self):
    now = datetime.now()
    one_day_later = now + timedelta(hours=24)
    worker_name = get_worker_name()
    task = TaskHistory.register(
        request=self.request, user=None, worker_name=worker_name)
    task.relevance = TaskHistory.RELEVANCE_CRITICAL
    try:
        scheudled_tasks = maintenance_models.TaskSchedule.objects.filter(
            status=maintenance_models.TaskSchedule.SCHEDULED,
            scheduled_for__day=one_day_later.day,
            scheduled_for__month=one_day_later.month,
            scheduled_for__year=one_day_later.year,
            scheduled_for__hour=one_day_later.hour,
        )
        for scheduled_task in scheudled_tasks:
            task.update_details(
                "Sendind mail for found for {} at {}...".format(
                    scheduled_task.database,
                    scheduled_task.scheduled_for),
                persist=True
            )
            scheduled_task.send_mail(
                is_new=False,
                is_execution_warning=True
            )
            task.update_details(
                "OK\n",
                persist=True
            )

        task.update_status_for(TaskHistory.STATUS_SUCCESS, details="\nDone")
    except Exception as err:
        task.update_status_for(
            TaskHistory.STATUS_ERROR, details=err
        )
        return


@app.task(bind=True)
@only_one(key="checksslexpireattask")
def check_ssl_expire_at(self):
    LOG.info("Retrieving all SSL MySQL databases")
    today = date.today()
    worker_name = get_worker_name()
    task = TaskHistory.register(
        request=self.request, user=None, worker_name=worker_name)
    task.relevance = TaskHistory.RELEVANCE_CRITICAL
    one_month_later = today + timedelta(days=30)
    check_ssl_envs = Configuration.get_by_name('check_ssl_envs')
    extra_filters = {}
    if check_ssl_envs:
        extra_filters = {'environment__name__in': check_ssl_envs.split(',')}
    try:
        infras = DatabaseInfra.objects.filter(
            ssl_configured=True,
            engine__engine_type__name__contains='mysql',
            instances__hostname__ssl_expire_at__lte=one_month_later,
            **extra_filters
        ).distinct()
        for infra in infras:
            database = infra.databases.first()

            task.update_details(
                "Checking database {}...".format(database), persist=True
            )
            scheudled_tasks = maintenance_models.TaskSchedule.objects.filter(
                Q(status=maintenance_models.TaskSchedule.SCHEDULED)
                | Q(status=maintenance_models.TaskSchedule.ERROR),
                scheduled_for__lte=one_month_later,
                database=database
            )
            if scheudled_tasks:
                task.update_details("Already scheduled!\n", persist=True)
            else:
                task_schedule = maintenance_models.TaskSchedule.objects.create(
                    method_path='update_ssl',
                    scheduled_for=maintenance_models.TaskSchedule.next_maintenance_window(  # noqa
                        today + timedelta(days=7),
                        infra.maintenance_window,
                        infra.maintenance_day
                    ),
                    database=database
                )
                task_schedule.send_mail(is_new=True)
                task.update_details("Schedule created!\n", persist=True)
        task.update_status_for(TaskHistory.STATUS_SUCCESS, details="\nDone")
    except Exception as err:
        task.update_status_for(TaskHistory.STATUS_ERROR, details=err)
        return


@app.task(bind=True)
@only_one(key="executescheduledmaintenancetask")
def execute_scheduled_maintenance(self, task=None, user=None):
    LOG.info("Searching Scheduled tasks")
    if user is None:
        user = User.objects.get(username='admin')
    if task:
        scheduled_tasks = [task]
    else:
        now = datetime.now()
        end_date = now.replace(minute=59)
        scheduled_tasks = maintenance_models.TaskSchedule.objects.filter(
            scheduled_for__lte=end_date,
            status=maintenance_models.TaskSchedule.SCHEDULED,
        )
    if scheduled_tasks:
        LOG.info("Scheduled Tasks Found!")
    for scheduled_task in scheduled_tasks:
        func = getattr(TaskRegister, scheduled_task.method_path)
        func(
            scheduled_task.database,
            user=user,
            scheduled_task=scheduled_task,
        )


def create_zabbix_alarms(database):
    LOG.info("{} alarms will be created!".format(database))
    zabbix_provider = handle_zabbix_alarms(database)
    zabbix_provider.create_basic_monitors()
    zabbix_provider.create_database_monitors()


def delete_zabbix_alarms(database):
    LOG.info("{} alarms will be deleted!".format(database))
    zabbix_provider = handle_zabbix_alarms(database)
    zabbix_provider.delete_basic_monitors()
    zabbix_provider.delete_database_monitors()


def handle_zabbix_alarms(database):
    from dbaas_zabbix import factory_for
    from dbaas_credentials.credential import Credential
    from dbaas_credentials.models import CredentialType
    integration = CredentialType.objects.get(type=CredentialType.ZABBIX)
    credentials = Credential.get_credentials(
        environment=database.databaseinfra.environment,
        integration=integration
    )

    return factory_for(
        databaseinfra=database.databaseinfra, credentials=credentials
    )


@app.task(bind=True)
def database_disk_resize(self, database, disk_offering, task_history, user):
    from workflow.steps.util.volume_provider import ResizeVolume

    AuditRequest.new_request("database_disk_resize", user, "localhost")

    if not database.pin_task(task_history):
        task_history.error_in_lock(database)
        return False

    databaseinfra = database.databaseinfra
    old_disk_offering = database.databaseinfra.disk_offering
    resized = []

    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, task_history=task_history,
            user=user, worker_name=worker_name
        )

        task_history.update_details(
            persist=True,
            details='\nLoading Disk offering'
        )

        databaseinfra.disk_offering = disk_offering
        databaseinfra.save()

        for instance in databaseinfra.get_driver().get_database_instances():

            task_history.update_details(
                persist=True,
                details='\nChanging instance {} to '
                        'NFS {}'.format(instance, disk_offering)
            )
            ResizeVolume(instance).do()
            resized.append(instance)

        task_history.update_details(
            persist=True,
            details='\nUpdate DBaaS metadata from {} to {}'.format(
                old_disk_offering, disk_offering
            )
        )

        task_history.update_status_for(
            status=TaskHistory.STATUS_SUCCESS,
            details='\nDisk resize successfully done.'
        )

        database.finish_task()
        return True

    except Exception as e:
        error = "Disk resize ERROR: {}".format(e)
        LOG.error(error)

        if databaseinfra.disk_offering != old_disk_offering:
            task_history.update_details(
                persist=True, details='\nUndo update DBaaS metadata'
            )
            databaseinfra.disk_offering = old_disk_offering
            databaseinfra.save()

        for instance in resized:
            task_history.update_details(
                persist=True,
                details='\nUndo NFS change for instance {}'.format(instance)
            )
            ResizeVolume(instance).do()
            resized.append(instance)

        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=error)
        database.finish_task()
    finally:
        AuditRequest.cleanup_request()


@app.task(bind=True)
@only_one(key="disk_auto_resize", timeout=600)
def update_disk_used_size(self):
    worker_name = get_worker_name()
    task = TaskHistory.register(
        request=self.request, user=None, worker_name=worker_name
    )
    task.relevance = TaskHistory.RELEVANCE_WARNING
    task.add_detail(message='Collecting disk used space from Zabbix')

    from .tasks_disk_resize import zabbix_collect_used_disk
    zabbix_collect_used_disk(task=task)


@app.task(bind=True)
def upgrade_database(self, database, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra
    source_plan = infra.plan
    target_plan = source_plan.engine_equivalent_plan

    class_path = target_plan.replication_topology.class_path
    steps = util_providers.get_database_upgrade_setting(class_path)

    database_upgrade = maintenance_models.DatabaseUpgrade()
    database_upgrade.database = database
    database_upgrade.source_plan = source_plan
    database_upgrade.target_plan = target_plan
    database_upgrade.task = task
    database_upgrade.save()

    hosts = []
    for instance in database.infra.instances.all():
        if instance.hostname not in hosts:
            hosts.append(instance.hostname)

    instances = []
    for host in hosts:
        instances.append(host.instances.all()[0])
    instances = instances

    success = steps_for_instances(
        steps, instances, task,
        database_upgrade.update_step, since_step
    )

    if success:
        infra.plan = target_plan
        infra.engine = target_plan.engine
        infra.engine_patch = target_plan.engine.default_engine_patch
        infra.save()

        database_upgrade.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_upgrade.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do upgrade.\nUpgrade doesn\'t have rollback'
        )


@app.task(bind=True)
def migrate_engine(self, database, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra
    source_plan = infra.plan
    target_plan = source_plan.migrate_engine_equivalent_plan

    class_path = target_plan.replication_topology.class_path
    steps = util_providers.get_engine_migrate_settings(class_path)

    database_migrate_engine_obj = maintenance_models.DatabaseMigrateEngine()
    database_migrate_engine_obj.database = database
    database_migrate_engine_obj.source_plan = source_plan
    database_migrate_engine_obj.target_plan = target_plan
    database_migrate_engine_obj.task = task
    database_migrate_engine_obj.current_database = database
    database_migrate_engine_obj.save()

    instances = database.infra.instances.all()

    success = steps_for_instances(
        steps, instances, task,
        database_migrate_engine_obj.update_step, since_step
    )

    if success:
        infra.plan = target_plan
        infra.engine = target_plan.engine
        infra.engine_patch = target_plan.engine.default_engine_patch
        infra.save()

        instance_type = getattr(
            Instance, target_plan.engine.engine_type.name.upper(), 0
        )

        # Setting new Instance Type for all instances
        infra.instances.update(instance_type=instance_type)

        database_migrate_engine_obj.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_migrate_engine_obj.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do migrate.\nMigrate Engine doesn\'t have rollback'
        )


@app.task(bind=True)
def upgrade_database_patch(self, database, patch, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra
    source_patch = infra.engine_patch
    target_patch = patch

    class_path = infra.plan.replication_topology.class_path
    steps = util_providers.get_database_upgrade_patch_setting(class_path)

    database_upgrade_patch = maintenance_models.DatabaseUpgradePatch()
    database_upgrade_patch.database = database
    database_upgrade_patch.source_patch = source_patch
    database_upgrade_patch.target_patch = target_patch
    database_upgrade_patch.task = task
    database_upgrade_patch.save()

    hosts = []
    for instance in database.infra.instances.all():
        if instance.hostname not in hosts:
            hosts.append(instance.hostname)

    instances = []
    for host in hosts:
        instances.append(host.instances.all()[0])
    instances = instances

    success = steps_for_instances(
        steps, instances, task,
        database_upgrade_patch.update_step, since_step
    )

    if success:
        infra.engine_patch = target_patch
        infra.save()

        database_upgrade_patch.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_upgrade_patch.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do upgrade patch.\nUpgrade patch doesn\'t have rollback'
        )


@app.task(bind=True)
def reinstall_vm_database(self, database, instance, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra

    class_path = infra.plan.replication_topology.class_path
    steps = util_providers.get_reinstallvm_steps_setting(class_path)

    database_reinstallvm = maintenance_models.DatabaseReinstallVM()
    database_reinstallvm.database = database
    database_reinstallvm.instance = instance
    database_reinstallvm.task = task
    database_reinstallvm.save()

    instances = [instance, ]

    success = steps_for_instances(
        steps, instances, task,
        database_reinstallvm.update_step, since_step
    )

    if success:
        database_reinstallvm.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_reinstallvm.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do reinstall vm.\nReinstall VM doesn\'t have rollback'
        )


@app.task(bind=True)
def change_parameters_database(self, database, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra
    plan = infra.plan
    class_path = plan.replication_topology.class_path

    from physical.models import DatabaseInfraParameter
    changed_parameters = (
        DatabaseInfraParameter.get_databaseinfra_changed_parameters(
            databaseinfra=infra,
        )
    )
    all_dinamic = True
    custom_procedure = None
    for changed_parameter in changed_parameters:
        if changed_parameter.parameter.dynamic is False:
            all_dinamic = False
            break
    for changed_parameter in changed_parameters:
        if changed_parameter.parameter.custom_method:
            custom_procedure = changed_parameter.parameter.custom_method
            break

    steps = util_providers.get_database_change_parameter_setting(
        class_path, all_dinamic, custom_procedure)

    LOG.info(steps)

    task.add_detail("Changed parameters:", level=0)
    for changed_parameter in changed_parameters:
        msg = "{}: old value: [{}], new value: [{}]".format(
            changed_parameter.parameter.name,
            changed_parameter.current_value,
            changed_parameter.value

        )
        task.add_detail(msg, level=1)
    task.add_detail("", level=0)

    if since_step > 0:
        steps_dec = (
            util_providers.get_database_change_parameter_retry_steps_count(
                class_path, all_dinamic, custom_procedure
            )
        )
        LOG.info('since_step: {}, steps_dec: {}'.format(since_step, steps_dec))
        since_step = since_step - steps_dec
        if since_step < 0:
            since_step = 0

    database_change_parameter = maintenance_models.DatabaseChangeParameter()
    database_change_parameter.database = database
    database_change_parameter.task = task
    database_change_parameter.save()

    instances_to_change_parameters = (
        infra.get_driver().get_database_instances()
    )

    success = steps_for_instances(
        steps, instances_to_change_parameters, task,
        database_change_parameter.update_step, since_step
    )

    if success:
        database_change_parameter.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_change_parameter.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            ('Could not do change the database parameters.\nChange '
             'parameters doesn\'t have rollback')
        )


@app.task(bind=True)
def add_instances_to_database(
    self, database, user, task, number_of_instances=1,
    number_of_instances_before_task=0, since_step=0
):
    from util.providers import get_add_database_instances_steps
    from util import get_vm_name

    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra
    plan = infra.plan
    driver = infra.get_driver()

    class_path = plan.replication_topology.class_path
    steps = get_add_database_instances_steps(class_path)

    add_instances_to_database_obj = maintenance_models.AddInstancesToDatabase()
    add_instances_to_database_obj.database = database
    add_instances_to_database_obj.task = task
    add_instances_to_database_obj.number_of_instances = number_of_instances
    add_instances_to_database_obj.number_of_instances_before = (
        number_of_instances_before_task
    )
    add_instances_to_database_obj.save()

    instances = []
    last_vm_created = number_of_instances_before_task

    for i in range(number_of_instances):
        instance = None
        last_vm_created += 1
        vm_name = get_vm_name(
            prefix=infra.name_prefix,
            sufix=infra.name_stamp,
            vm_number=last_vm_created
        )

        try:
            instance = infra.instances.get(
                Q(hostname__hostname__startswith=vm_name) |
                Q(dns__startswith=vm_name),
                port=driver.get_default_database_port(),
            )
        except Instance.DoesNotExist:
            instance = Instance(
                databaseinfra=infra,
                dns=vm_name,
                port=driver.get_default_database_port(),
                instance_type=driver.get_default_instance_type()
            )

        instance.vm_name = instance.dns
        instances.append(instance)

    success = steps_for_instances(
        steps, instances, task,
        step_counter_method=add_instances_to_database_obj.update_step,
        since_step=since_step
    )

    if success:
        add_instances_to_database_obj.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        add_instances_to_database_obj.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do add instance(s) to database.'
        )


@app.task(bind=True)
def add_instances_to_database_rollback(self, manager_obj, user, task):
    from util.providers import get_add_database_instances_steps
    from util import get_vm_name

    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = manager_obj.database.infra
    plan = infra.plan
    driver = infra.get_driver()

    class_path = plan.replication_topology.class_path
    steps = get_add_database_instances_steps(class_path)

    manager_obj.id = None
    manager_obj.created_at = None
    manager_obj.finished_at = None
    manager_obj.task = task
    manager_obj.current_step -= 1
    manager_obj.save()

    instances = []
    last_vm_created = manager_obj.number_of_instances_before

    for i in range(manager_obj.number_of_instances):
        instance = None
        last_vm_created += 1
        vm_name = get_vm_name(
            prefix=infra.name_prefix,
            sufix=infra.name_stamp,
            vm_number=last_vm_created
        )

        try:
            instance = infra.instances.get(
                Q(hostname__hostname__startswith=vm_name) |
                Q(dns__startswith=vm_name),
                port=driver.get_default_database_port(),
            )
        except Instance.DoesNotExist:
            instance = Instance(
                databaseinfra=infra,
                dns=vm_name,
                port=driver.get_default_database_port(),
                instance_type=driver.get_default_instance_type()
            )

        instance.vm_name = instance.dns
        instances.append(instance)

    success = rollback_for_instances_full(
        steps, instances, task,
        manager_obj.get_current_step, manager_obj.update_step
    )

    if success:
        manager_obj.set_rollback()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done.')
    else:
        manager_obj.current_step += 1
        manager_obj.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do rollback\n'
            'Please check error message and do retry'
        )


@app.task(bind=True)
def remove_readonly_instance(self, instance, user, task):
    from workflow.workflow import steps_for_instances
    from util.providers import get_remove_readonly_instance_steps

    infra = instance.databaseinfra
    database = infra.databases.last()

    self.request.kwargs['database'] = database
    self.request.kwargs['instance'] = instance
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    plan = infra.plan

    class_path = plan.replication_topology.class_path
    steps = get_remove_readonly_instance_steps(class_path)

    instances = []
    instances.append(instance)

    success = steps_for_instances(
        list_of_groups_of_steps=steps,
        instances=instances,
        task=task,
        undo=True
    )

    if success:
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        task.update_status_for(TaskHistory.STATUS_ERROR, 'Done')


@app.task(bind=True)
def resize_database(self, database, user, task, offering,
                    original_offering=None, since_step=0):

    self.request.kwargs['database'] = database
    self.request.kwargs['offering'] = offering

    worker_name = get_worker_name()
    task = TaskHistory.register(
        self.request, user, task,
        worker_name,
    )

    infra = database.infra

    if not original_offering:
        original_offering = database.infra.offering

    database_resize = maintenance_models.DatabaseResize(
        database=database,
        source_offer=original_offering,
        target_offer=offering,
        task=task
    )

    class_path = infra.plan.replication_topology.class_path
    steps = util_providers.get_resize_settings(class_path)

    instances_to_resize = infra.get_driver().get_database_instances()
    success = steps_for_instances(
        steps, instances_to_resize, task,
        database_resize.update_step, since_step
    )

    if success:
        database_resize.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done.')
    else:
        database_resize.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do resize.\n'
            'Please check the task log and execute rollback or retry'
        )


@app.task(bind=True)
def resize_database_rollback(self, from_resize, user, task):
    self.request.kwargs['database'] = from_resize.database
    self.request.kwargs['target_offer'] = from_resize.target_offer
    task = TaskHistory.register(self.request, user, task, get_worker_name())

    infra = from_resize.database.infra

    class_path = infra.plan.replication_topology.class_path
    steps = util_providers.get_resize_settings(class_path)

    instances = list(infra.get_driver().get_database_instances())

    from_resize.id = None
    from_resize.task = task
    from_resize.current_step -= 1
    from_resize.save()

    success = rollback_for_instances_full(
        steps, instances, task,
        from_resize.get_current_step, from_resize.update_step
    )

    if success:
        from_resize.set_rollback()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done.')
    else:
        from_resize.current_step += 1
        from_resize.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            'Could not do rollback\n'
            'Please check error message and do retry'
        )


@app.task(bind=True)
def switch_write_database(self, database, instance, user, task):
    from workflow.workflow import steps_for_instances
    from util.providers import get_switch_write_instance_steps

    self.request.kwargs['database'] = database
    self.request.kwargs['instance'] = instance
    infra = instance.databaseinfra

    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    plan = infra.plan

    class_path = plan.replication_topology.class_path
    steps = get_switch_write_instance_steps(class_path)

    instances = []
    instances.append(instance)

    success = steps_for_instances(
        list_of_groups_of_steps=steps,
        instances=instances,
        task=task
    )

    if success:
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        task.update_status_for(TaskHistory.STATUS_ERROR, 'Done')
        database.finish_task()


@app.task(bind=True)
def configure_ssl_database(self, database, user, task, since_step=0):
    worker_name = get_worker_name()
    task = TaskHistory.register(self.request, user, task, worker_name)

    infra = database.infra

    class_path = infra.plan.replication_topology.class_path
    steps = util_providers.get_database_configure_ssl_setting(class_path)

    database_configure_ssl = maintenance_models.DatabaseConfigureSSL()
    database_configure_ssl.database = database
    database_configure_ssl.task = task
    database_configure_ssl.save()

    instances = list(infra.get_driver().get_database_instances())

    success = steps_for_instances(
        steps, instances, task,
        database_configure_ssl.update_step, since_step
    )

    if success:
        database_configure_ssl.set_success()
        task.update_status_for(TaskHistory.STATUS_SUCCESS, 'Done')
    else:
        database_configure_ssl.set_error()
        task.update_status_for(
            TaskHistory.STATUS_ERROR,
            ('Could not do have SSL configured.\nConfigure SSL doesn\'t '
             'have rollback')
        )


@app.task(bind=True)
def update_database_monitoring(self, task, database, hostgroup, action):
    from workflow.steps.util.zabbix import UpdateMonitoringRemoveHostgroup
    from workflow.steps.util.zabbix import UpdateMonitoringAddHostgroup

    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, task_history=task
    )
    detail = 'Update database monitoring, {} hostgroup '.format(action)
    task_history.add_detail(detail)

    try:

        databaseinfra = database.databaseinfra
        for instance in databaseinfra.instances.all():

            detail = '{} hostgroup for {}'.format(action, instance)
            task_history.add_detail(detail, level=2)

            if action == 'add':
                UpdateMonitoringAddHostgroup(instance, hostgroup).do()
            elif action == 'remove':
                UpdateMonitoringRemoveHostgroup(instance, hostgroup).do()

    except Exception as e:
        task_history.add_detail('Error: {}'.format(e))
        task.set_status_error('Could not update monitoring')
        return False

    else:
        task.set_status_success('Monitoring updated with success')
        return True


@app.task(bind=True)
def update_organization_name_monitoring(self, task, database,
                                        organization_name):
    from workflow.steps.util.db_monitor import UpdateInfraOrganizationName

    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name, task_history=task
    )
    detail = 'Update organization name on monitoring'
    task_history.add_detail(detail)

    try:
        databaseinfra = database.databaseinfra
        for instance in databaseinfra.instances.all():

            detail = 'update organization name:{} for {}'.format(
                organization_name, instance)
            task_history.add_detail(detail, level=2)
            UpdateInfraOrganizationName(instance, organization_name).do()

    except Exception as e:
        task_history.add_detail('Error: {}'.format(e))
        task.set_status_error('Could not update monitoring')
        return False

    else:
        task.set_status_success('Monitoring updated with success')
        return True


class TaskRegister(object):
    TASK_CLASS = TaskHistory

    @classmethod
    def create_task(cls, params):
        database = params.pop('database', None)

        task = cls.TASK_CLASS()

        if database:
            task.object_id = database.id
            task.object_class = database._meta.db_table
            database_name = database.name
        else:
            database_name = params.pop('database_name', '')

        task.database_name = database_name

        for k, v in params.iteritems():
            setattr(task, k, v)

        task.save()

        return task

    # ============  BEGIN TASKS   ==========

    @classmethod
    def database_disk_resize(cls,
                             database,
                             user,
                             disk_offering,
                             task_name=None,
                             register_user=True,
                             **kw):

        task_params = {
            'task_name': ('database_disk_resize' if task_name is None
                          else task_name),
            'arguments': 'Database name: {}'.format(database.name),
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task_params.update(**{'user': user} if register_user else {})
        task = cls.create_task(task_params)
        database_disk_resize.delay(
            database=database,
            user=user,
            disk_offering=disk_offering,
            task_history=task
        )

        return task

    @classmethod
    def database_destroy(cls, database, user, **kw):
        task_params = {
            'task_name': 'destroy_database',
            'arguments': 'Database name: {}'.format(database.name),
            'user': user,
            'database': database
        }

        task = cls.create_task(task_params)
        destroy_database.delay(database=database, user=user, task_history=task)

    @classmethod
    def database_resize(cls, database, user, offering, **kw):
        task_params = {
            'task_name': 'resize_database',
            'arguments': 'Database name: {}'.format(database.name),
            'user': user,
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)
        resize_database.delay(
            database=database,
            user=user,
            task=task,
            offering=offering
        )

    @classmethod
    def database_resize_retry(cls,
                              database,
                              user,
                              offering,
                              original_offering,
                              since_step,
                              **kw):
        task_params = {
            'task_name': 'resize_database_retry',
            'arguments': "Retrying resize database {}".format(database),
            'user': user,
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)
        resize_database.delay(
            database=database,
            user=user,
            task=task,
            offering=offering,
            original_offering=original_offering,
            since_step=since_step
        )

    @classmethod
    def database_resize_rollback(
            cls, from_resize, user
    ):
        task_params = {
            'task_name': 'resize_database_rollback',
            'arguments': "Rollback resize database {}".format(
                from_resize.database),
            'user': user,
            'database': from_resize.database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)
        resize_database_rollback.delay(from_resize, user, task)

    @classmethod
    def database_add_instances(
        cls, database, user, number_of_instances,
        number_of_instances_before_task, since_step=None
    ):
        task_params = {
            'task_name': 'add_database_instances',
            'arguments': "Adding instances on database {}".format(database),
            'user': user,
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'add_database_instances_retry'
            task_params['arguments'] = (
                'Retrying to add instances to database {}'.format(database)
            )

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'task': task,
            'user': user,
            'number_of_instances': number_of_instances,
            'number_of_instances_before_task': number_of_instances_before_task
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        add_instances_to_database.delay(**delay_params)

    @classmethod
    def database_add_instances_rollback(
        cls, manager_obj, user
    ):
        task_params = {
            'task_name': 'resize_database_rollback',
            'arguments': "Rollback Add Instance to database {}".format(
                manager_obj.database
            ),
            'user': user,
            'database': manager_obj.database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)
        add_instances_to_database_rollback.delay(manager_obj, user, task)

    @classmethod
    def database_remove_instance(cls, database, user, instance):
        task_params = {
            'task_name': "remove_database_instance",
            'arguments': "Removing instance {} on database {}".format(
                instance, database),
            'user': user,
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)

        remove_readonly_instance.delay(
            instance=instance,
            user=user,
            task=task,
        )

    @classmethod
    def databases_analyze(cls):
        from dbaas_services.analyzing.tasks import analyze_databases

        task_params = {
            'task_name': 'analyze_databases',
            'arguments': "Waiting to start",
            'relevance': TaskHistory.RELEVANCE_WARNING
        }
        task = cls.create_task(task_params)
        analyze_databases.delay(task_history=task)

    @classmethod
    def database_clone(cls, origin_database, user, clone_name,
                       plan, environment, retry_from=None):

        task_params = {
            'task_name': 'clone_database',
            'arguments': 'Database name: {}'.format(origin_database.name),
            'user': user,
            'database': origin_database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }
        task = cls.create_task(task_params)

        clone_database.delay(
            origin_database=origin_database, user=user, clone_name=clone_name,
            plan=plan, environment=environment, task_history=task,
            retry_from=retry_from
        )

    @classmethod
    def database_create(cls, user, name, plan, environment, team,
                        project, description, backup_hour=2,
                        maintenance_window=1, maintenance_day=1,
                        subscribe_to_email_events=True, register_user=True,
                        is_protected=False, retry_from=None):
        task_params = {
            'task_name': "create_database",
            'arguments': "Database name: {}".format(name),
            'database_name': name,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }
        task_params.update(**{'user': user} if register_user else {})
        task = cls.create_task(task_params)

        return create_database_with_retry(
            name=name, plan=plan, environment=environment, team=team,
            project=project, description=description, task=task,
            backup_hour=backup_hour, maintenance_window=maintenance_window,
            maintenance_day=maintenance_day,
            subscribe_to_email_events=subscribe_to_email_events,
            is_protected=is_protected, user=user, retry_from=retry_from
        )

    @classmethod
    def database_create_rollback(cls, rollback_from, user,
                                 extra_task_params=None):
        task_params = {
            'task_name': "create_database",
            'arguments': "Database name: {}".format(rollback_from.name),
            'database_name': rollback_from.name,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }
        task_params.update(extra_task_params if extra_task_params else {})
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)

        from maintenance.tasks import create_database_rollback
        return create_database_rollback.delay(
            rollback_from=rollback_from, task=task, user=user
        )

    @classmethod
    def database_clone_rollback(cls, rollback_from, user,
                                extra_task_params=None):
        task_params = {
            'task_name': "clone_database_rollback",
            'arguments': "Database name: {}".format(rollback_from.name),
            'database_name': rollback_from.name,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }
        task_params.update(extra_task_params if extra_task_params else {})
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)

        return clone_database_rollback.delay(
            rollback_from=rollback_from, task=task, user=user,
        )

    @classmethod
    def database_destroy_retry(cls, rollback_from, user):
        task_params = {
            'task_name': "destroy_database_retry",
            'arguments': "Database name: {}".format(rollback_from.name),
            'database_name': rollback_from.name,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)

        return destroy_database_retry.delay(
            rollback_from=rollback_from, task=task, user=user
        )

    @classmethod
    def database_backup(cls, database, user):
        from backup.tasks import make_database_backup

        task_params = {
            'task_name': "make_database_backup",
            'arguments': "Making backup of {}".format(database),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)

        make_database_backup.delay(
            database=database,
            task=task
        )

    @classmethod
    def database_remove_backup(cls, database, snapshot, user):
        from backup.tasks import remove_database_backup

        task_params = {
            'task_name': "remove_database_backup",
            'arguments': "Remove backup of {}".format(database),
            'user': user,
            'relevance': TaskHistory.RELEVANCE_WARNING
        }

        task = cls.create_task(task_params)

        remove_database_backup.delay(
            snapshot=snapshot,
            task=task
        )

    @classmethod
    def restore_snapshot(cls, database, user, snapshot, retry_from=None):
        task_params = {
            'task_name': "restore_snapshot",
            'arguments': "Restoring {} to an older version.".format(
                          database.name),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)

        maintenace_tasks.restore_database.delay(
            database=database, task=task, snapshot=snapshot, user=user,
            retry_from=retry_from
        )

    @classmethod
    def database_upgrade(cls, database, user, since_step=None):

        task_params = {
            'task_name': 'upgrade_database',
            'arguments': 'Upgrading database {}'.format(database),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'upgrade_database_retry'
            task_params['arguments'] = 'Retrying upgrade database {}'.format(
                database
            )

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        upgrade_database.delay(**delay_params)

    @classmethod
    def engine_migrate(cls, database, target_plan, user, since_step=None):

        task_params = {
            'task_name': 'migrate_engine',
            'arguments': 'Migrate engine from database {}'.format(database),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'migrate_engine_retry'
            task_params['arguments'] = ('Retrying migrate engine from '
                                        'database {}').format(database)

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        migrate_engine.delay(**delay_params)

    @classmethod
    def database_upgrade_patch(cls, database, patch, user, since_step=None):

        task_params = {
            'task_name': 'upgrade_database_patch',
            'arguments': 'Upgrading database patch {}'.format(database),
            'database': database,
            'user': user,
            'patch': patch,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'upgrade_database_patch_retry'
            task_params['arguments'] = ('Retrying upgrade database '
                                        'patch {}').format(database)

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'patch': patch,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        upgrade_database_patch.delay(**delay_params)

    @classmethod
    def database_reinstall_vm(cls, instance, user, since_step=None):

        database = instance.databaseinfra.databases.first()
        task_params = {
            'task_name': 'reinstall_vm_database',
            'arguments': 'Reinstall VM for database {} and instance {}'.format(
                database, instance),
            'database': database,
            'instance': instance,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'reinstall_vm_database_retry'
            task_params['arguments'] = ('Retrying reinstall VM for database '
                                        '{} and instance {}').format(
                                            database, instance)

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'instance': instance,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        reinstall_vm_database.delay(**delay_params)

    @classmethod
    def database_change_parameters(cls, database, user, since_step=None):
        task_params = {
            'task_name': 'change_parameters',
            'arguments': 'Changing parameters of database {}'.format(database),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'change_parameters_retry'
            task_params['arguments'] = ('Retrying changing parameters of '
                                        'database {}').format(database)

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        change_parameters_database.delay(**delay_params)

    @classmethod
    def database_switch_write(cls, database, user, instance):
        task_params = {
            'task_name': "switch_write_database",
            'arguments': "Switching write instance {} on database {}".format(
                instance, database),
            'user': user,
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task = cls.create_task(task_params)

        switch_write_database.delay(
            database=database,
            instance=instance,
            user=user,
            task=task,
        )

    @classmethod
    def purge_unused_exports(cls, user='admin'):
        task_params = {
            'task_name': "purge_unused_exports",
            'arguments': "Removing unused exports",
            'user': user,
            'relevance': TaskHistory.RELEVANCE_WARNING
        }

        return cls.create_task(task_params)

    @classmethod
    def database_configure_ssl(cls, database, user, since_step=None):

        task_params = {
            'task_name': 'configure_ssl_database',
            'arguments': 'Configure SSL database {}'.format(database),
            'database': database,
            'user': user,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        if since_step:
            task_params['task_name'] = 'configure_ssl_database_retry'
            task_params['arguments'] = ('Retrying configure SSL database '
                                        '{}').format(database)

        task = cls.create_task(task_params)

        delay_params = {
            'database': database,
            'task': task,
            'user': user
        }

        delay_params.update(**{'since_step': since_step} if since_step else {})

        configure_ssl_database.delay(**delay_params)

    @classmethod
    def host_migrate(cls, host, zone, new_environment, user,
                     since_step=None, step_manager=None):
        task_params = {
            'task_name': "host_migrate",
            'arguments': "Host: {}, Zone: {}, New Environment: {}".format(
                host, zone, new_environment
            ),
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        return maintenace_tasks.node_zone_migrate.delay(
            host=host, zone=zone, new_environment=new_environment, task=task,
            since_step=since_step, step_manager=step_manager
        )

    @classmethod
    def recreate_slave(cls, host, user,
                       since_step=None, step_manager=None):
        db = Database.objects.get(databaseinfra__instances__hostname=host)
        task_params = {
            'task_name': "recreate_slave",
            'arguments': "Database: {}, Host: {}".format(
                db.name, host
            ),
            'database': db
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        return maintenace_tasks.recreate_slave.delay(
            database=db,
            host=host, task=task,
            since_step=since_step,
            step_manager=step_manager
        )

    @classmethod
    def update_ssl(cls, database, user,
                   since_step=None, step_manager=None, scheduled_task=None,
                   **kw):
        task_params = {
            'task_name': "update_ssl",
            'arguments': "Database: {}".format(
                database
            ),
        }
        auto_rollback = False
        if user:
            task_params['user'] = user
        if scheduled_task:
            auto_rollback = True
        task = cls.create_task(task_params)
        return maintenace_tasks.update_ssl.delay(
            database=database, task=task,
            since_step=since_step,
            step_manager=step_manager,
            auto_rollback=auto_rollback,
            scheduled_task=scheduled_task,
            **kw
        )

    @classmethod
    def restart_database(cls, database, user,
                         since_step=None, step_manager=None,
                         scheduled_task=None, **kw):
        task_params = {
            'task_name': "restart_database",
            'arguments': "Database: {}".format(
                database
            ),
        }
        auto_rollback = kw.get('auto_rollback')
        auto_cleanup = kw.get('auto_cleanup')
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        if scheduled_task:
            auto_rollback = False
            auto_cleanup = True
        return maintenace_tasks.restart_database.delay(
            database=database, task=task,
            since_step=since_step,
            step_manager=step_manager,
            auto_rollback=auto_rollback,
            auto_cleanup=auto_cleanup,
            scheduled_task=scheduled_task,
            **kw
        )

    @classmethod
    def host_migrate_rollback(cls, migrate, user):
        task_params = {
            'task_name': "host_migrate",
            'arguments': "Host: {}, Zone: {}, New Environment: {}".format(
                migrate.host, migrate.zone, migrate.environment
            ),
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        return maintenace_tasks.node_zone_migrate_rollback.delay(migrate, task)

    @classmethod
    def database_migrate(
        cls, database, new_environment, new_offering, user, hosts_zones,
        since_step=None, step_manager=None
    ):
        task_params = {
            'task_name': "database_migrate",
            'arguments': "Database: {}, Environment: {}".format(
                database, new_environment
            ),
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        return maintenace_tasks.database_environment_migrate.delay(
            database=database, new_environment=new_environment,
            new_offering=new_offering, task=task,
            hosts_zones=hosts_zones, since_step=since_step,
            step_manager=step_manager
        )

    @classmethod
    def database_migrate_rollback(cls, migrate, user):
        task_params = {
            'task_name': "database_migrate",
            'arguments': "Database: {}, Environment: {}".format(
                migrate.database, migrate.environment
            ),
        }
        if user:
            task_params['user'] = user
        task = cls.create_task(task_params)
        return maintenace_tasks.database_environment_migrate_rollback.delay(
            migrate, task
        )

    @classmethod
    def update_database_monitoring(cls, database, hostgroup, action):

        if action not in ('add', 'remove'):
            error = "{} is not a valid action.".format(action)
            error += " Valid actions are 'add' and 'remove'"
            LOG.error(error)
            return

        args = "Database: {}, Hostgroup: {}, Action: {}".format(
                database, hostgroup, action)
        task_params = {
            'task_name': "update_database_monitoring",
            'arguments': args,
            'relevance': TaskHistory.RELEVANCE_ERROR
        }

        task = cls.create_task(task_params)

        update_database_monitoring.delay(
            task=task,
            database=database,
            hostgroup=hostgroup,
            action=action,
        )

    @classmethod
    def update_organization_name_monitoring(cls, database, organization_name):

        args = "Database: {}, Organization Name: {}".format(
                database, organization_name)
        task_params = {
            'task_name': "update_organization_name_monitoring",
            'arguments': args,
            'relevance': TaskHistory.RELEVANCE_ERROR
        }

        task = cls.create_task(task_params)

        update_organization_name_monitoring.delay(
            task=task,
            database=database,
            organization_name=organization_name
        )

    # ============  END TASKS   ============
