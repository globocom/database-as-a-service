# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from datetime import datetime

from copy import copy

from django.db import models
from django.utils.translation import ugettext_lazy as _
from dateutil import rrule, tz
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from celery.task import control


from account.models import Team
from backup.models import BackupGroup, Snapshot
from logical.models import Database, Project
from physical.models import (
    Host, Plan, Environment, DatabaseInfra, Instance,
    Offering, EnginePatch)
from notification.models import TaskHistory
from util.models import BaseModel
from maintenance.tasks import execute_scheduled_maintenance
from .registered_functions.functools import _get_registered_functions
from .managers import DatabaseMaintenanceTaskManager
from util.email_notifications import schedule_task_notification
from system.models import Configuration
from dbaas.helpers import EmailHelper


LOG = logging.getLogger(__name__)


class Maintenance(BaseModel):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2
    REJECTED = 3
    REVOKED = 4

    MAINTENANCE_STATUS = (
        (FINISHED, 'Finished'),
        (RUNNING, 'Running'),
        (WAITING, 'Waiting'),
        (REJECTED, 'Rejected'),
        (REVOKED, 'Revoked')
    )

    description = models.CharField(null=False, blank=False, max_length=500)
    scheduled_for = models.DateTimeField(unique=True)
    main_script = models.TextField(null=False, blank=False)
    rollback_script = models.TextField(null=True, blank=True)
    maximum_workers = models.PositiveSmallIntegerField(null=False, default=1)
    celery_task_id = models.CharField(null=True, blank=True, max_length=50)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    affected_hosts = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    hostsid = models.CommaSeparatedIntegerField(
        verbose_name="Hosts id", null=False, blank=False, max_length=10000
    )
    created_by = models.CharField(max_length=255, null=True, blank=True)
    revoked_by = models.CharField(max_length=255, null=True, blank=True)
    disable_alarms = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s" % self.description

    class Meta:
        permissions = (
            ("view_maintenance", "Can view maintenance"),
        )

    def save_host_maintenance(self,):
        save_host_ok = True
        total_hosts = 0

        try:
            hostsid_list = self.hostsid.split(',')
            hosts = Host.objects.filter(pk__in=hostsid_list)
            for host in hosts:
                hm = HostMaintenance()
                hm.host = host
                hm.maintenance = self
                hm.hostname = host.hostname
                hm.save()
                total_hosts += 1

        except Exception as e:
            error = e.args[1]
            LOG.warn("Error: {}".format(error))
            self.status = self.REJECTED
            save_host_ok = False

        else:
            self.affected_hosts = total_hosts
            self.status = self.WAITING

        finally:
            # post_save signal has to be disconnected in order to avoid
            # recursive signal call
            post_save.disconnect(maintenance_post_save, sender=Maintenance)

            self.save()

            # connecting signal again
            post_save.connect(maintenance_post_save, sender=Maintenance)

        return save_host_ok

    def revoke_maintenance(self, request):
        if self.is_waiting_to_run:
            control.revoke(self.celery_task_id,)

            self.status = self.REVOKED
            self.revoked_by = request.user.username
            self.save()

            HostMaintenance.objects.filter(maintenance=self).update(
                status=HostMaintenance.REVOKED
            )
            return True

        return False

    def is_waiting_to_run(self):
        if self.status == self.FINISHED:
            LOG.info("Maintenance: {} has already run!".format(self))
            return False
        elif self.status == self.REJECTED:
            LOG.info("Maintenance: {} has been rejected".format(self))
            return False

        inspect = control.inspect()
        scheduled_tasks = inspect.scheduled()
        try:
            hosts = scheduled_tasks.keys()
        except Exception as e:
            LOG.info("Could not retrieve celery scheduled tasks: {}".format(e))
            return False

        for host in hosts:
            try:
                scheduled_tasks = scheduled_tasks[host]
            except TypeError:
                LOG.warn("There are no scheduled tasks")
                LOG.info(scheduled_tasks)
                continue

            for task in scheduled_tasks:
                if task['request']['id'] == self.celery_task_id:
                    return True

        return False


class TaskSchedule(BaseModel):
    subject_tmpl = '[DBaaS] Automatic Task {} for Database {}'
    email_helper = EmailHelper
    SCHEDULED = 0
    RUNNING = 1
    SUCCESS = 2
    ERROR = 3

    STATUS = (
        (SCHEDULED, 'Scheduled'),
        (RUNNING, 'Running'),
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
    )

    method_path = models.CharField(null=False, blank=False, max_length=500)
    status = models.IntegerField(choices=STATUS, default=SCHEDULED)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    database = models.ForeignKey(Database, related_name='task_schedules')

    def __unicode__(self):
        return "path: {} | scheduled_for: {}".format(
            self.method_path, self.scheduled_for
        )

    @property
    def status_label(self):
        if self.status is not None:
            return dict(self.STATUS)[self.status]

    def is_valid(self):
        scheduled_date = self.scheduled_for.date()
        expire_at = self.database.infra.earliest_ssl_expire_at
        now = datetime.now()
        if expire_at and (scheduled_date >= expire_at):
            msg = ('You cant schedule greater or equal then ssl expire. '
                   'Scheduled for: {} Expire at: {}'.format(
                        scheduled_date, expire_at)
                   )
            return False, msg
        if (self.scheduled_for < now):
            msg = 'You cant schedule less then now.'
            return False, msg

        return True, ''

    class Meta:
        permissions = (
            ("view_maintenance", "Can view maintenance"),
        )

    @staticmethod
    def next_maintenance_window(start_date, maintenance_hour, weekday):
        weekdays = list(copy(rrule.weekdays))
        weekdays.insert(0, weekdays.pop())
        rule = rrule.rrule(
            rrule.DAILY,
            byweekday=[weekdays[weekday]],
            dtstart=start_date
        )
        ruleset = rrule.rruleset()
        ruleset.rrule(rule)
        schedule_datetime = ruleset[0]
        schedule_datetime = schedule_datetime.replace(hour=maintenance_hour)
        return schedule_datetime

    def _set_status(self, status):
        self.status = status
        self.save()

    def set_success(self):
        self.finished_at = datetime.now()
        self._set_status(self.SUCCESS)

    def set_error(self):
        self.finished_at = datetime.now()
        self._set_status(self.ERROR)

    def set_running(self):
        self.started_at = datetime.now()
        self._set_status(self.RUNNING)

    def send_mail(self, is_new=False, is_execution_warning=None,
                  template_name=None):
        if template_name is None:
            template_name = '{}_notification'.format(self.method_path)

        if is_execution_warning:
            action = 'execution warning'
        elif is_new:
            action = 'created'
        else:
            action = 'updated'

        subject = _(self.subject_tmpl.format(
            action,
            self.database.name,
        ))

        domain = self.email_helper.get_domain()
        template_context = {
            'database': self.database,
            'scheduled_for': self.scheduled_for,
            'is_execution_warning': is_execution_warning,
            'ssl_expire_at': self.database.infra.earliest_ssl_expire_at,
            'database_url': "{}{}".format(
                domain,
                reverse(
                    'admin:logical_database_maintenance',
                    kwargs={'id': self.database.id}
                )
            ),
            'is_new': is_new,
            'is_ha': self.database.infra.plan.is_ha,
            'domain': domain,
            'include_template_name_txt': 'email_extras/{}.txt'.format(
                template_name
            ),
            'include_template_name_html': 'email_extras/{}.html'.format(
                template_name
            ),
        }

        self.email_helper.send_mail(
            subject=subject,
            template_name='schedule_task_notification',
            template_context=template_context,
            action=self.method_path,
            database=self.database,
        )


class HostMaintenance(BaseModel):
    ERROR = 0
    SUCCESS = 1
    RUNNING = 2
    ROLLBACK = 3
    WAITING = 4
    ROLLBACK_ERROR = 5
    ROLLBACK_SUCCESS = 6
    REVOKED = 7
    UNAVAILABLEHOST = 8
    UNAVAILABLECSHOSTATTR = 9

    MAINTENANCE_STATUS = (
        (ERROR, 'Error'),
        (SUCCESS, 'Success'),
        (RUNNING, 'Running'),
        (ROLLBACK, 'Rollback'),
        (WAITING, 'Waiting'),
        (ROLLBACK_ERROR, 'Rollback error'),
        (ROLLBACK_SUCCESS, 'Rollback success'),
        (REVOKED, 'Revoked'),
        (UNAVAILABLEHOST, 'Unavailable host'),
        (UNAVAILABLECSHOSTATTR, 'Unavailable cloudstack host attr'),
    )

    started_at = models.DateTimeField(verbose_name=_("Started at"), null=True)
    finished_at = models.DateTimeField(
        verbose_name=_("Finished at"), null=True)
    main_log = models.TextField(verbose_name=_("Main Log"),
                                null=True, blank=True)
    rollback_log = models.TextField(verbose_name=_("Rollback Log"),
                                    null=True, blank=True)
    status = models.IntegerField(choices=MAINTENANCE_STATUS, default=WAITING)
    host = models.ForeignKey(Host, related_name="host_maintenance",
                             on_delete=models.SET_NULL, null=True)
    hostname = models.CharField(verbose_name=_("Hostname"), max_length=255,
                                default='')
    maintenance = models.ForeignKey(Maintenance, related_name="maintenance",)

    class Meta:
        unique_together = (("host", "maintenance"),)
        index_together = [["host", "maintenance"], ]
        permissions = (
            ("view_hostmaintenance", "Can view host maintenance"),
        )

    def __unicode__(self):
        return "%s %s" % (self.host, self.maintenance)


class MaintenanceParameters(BaseModel):
    parameter_name = models.CharField(null=False, blank=False, max_length=100)
    function_name = models.CharField(
        null=False, blank=False, max_length=100,
        choices=(_get_registered_functions())
    )
    maintenance = models.ForeignKey(
        Maintenance, related_name="maintenance_params"
    )

    def __unicode__(self):
        return "{} - {}".format(self.parameter_name, self.function_name)

    class Meta:
        permissions = (
            ("view_maintenance_parameters", "Can view maintenance parameters"),
        )


class DatabaseMaintenanceTask(BaseModel):
    WAITING = 0
    RUNNING = 1
    ERROR = 2
    SUCCESS = 3
    ROLLBACK = 4
    STATUS = (
        (WAITING, 'Waiting'),
        (RUNNING, 'Running'),
        (ERROR, 'Error'),
        (SUCCESS, 'Success'),
        (ROLLBACK, 'Rollback'),
    )

    current_step = models.PositiveSmallIntegerField(
        verbose_name="Current Step", null=False, blank=False, default=0
    )
    status = models.IntegerField(
        verbose_name="Status", choices=STATUS, default=WAITING
    )
    started_at = models.DateTimeField(
        verbose_name="Started at", null=True, blank=True
    )
    finished_at = models.DateTimeField(
        verbose_name="Finished at", null=True, blank=True
    )
    can_do_retry = models.BooleanField(
        verbose_name=_("Can Do Retry"), default=True
    )
    task_schedule = models.ForeignKey(
        'TaskSchedule',
        null=True, blank=True, unique=False,
        related_name="%(app_label)s_%(class)s_related"
    )
    objects = DatabaseMaintenanceTaskManager()

    def get_current_step(self):
        return self.current_step

    def update_step(self, step):
        if not self.started_at:
            self.started_at = datetime.now()

        self.status = self.RUNNING
        self.current_step = step
        self.save()

    def update_final_status(self, status):
        self.finished_at = datetime.now()
        self.status = status
        self.save()

    def set_success(self):
        self.update_final_status(self.SUCCESS)
        if self.task_schedule:
            self.task_schedule.set_success()

    def set_running(self):
        self.update_final_status(self.RUNNING)
        if self.task_schedule:
            self.task_schedule.set_running()

    def set_error(self):
        self.update_final_status(self.ERROR)
        if self.task_schedule:
            self.task_schedule.set_error()

    def set_rollback(self):
        self.can_do_retry = False
        self.update_final_status(self.ROLLBACK)

    @property
    def is_status_error(self):
        return self.status == self.ERROR

    @property
    def is_status_success(self):
        return self.status == self.SUCCESS

    @property
    def is_running(self):
        return self.status == self.RUNNING

    @property
    def disable_retry_filter(self):
        return {'database': self.database}

    def save(self, *args, **kwargs):
        super(DatabaseMaintenanceTask, self).save(*args, **kwargs)

        older = self.__class__.objects.filter(
            **self.disable_retry_filter
        ).exclude(
            id=self.id
        )
        older.update(can_do_retry=False)

    class Meta:
        abstract = True


class DatabaseUpgrade(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="upgrades"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_upgrades"
    )
    source_plan = models.ForeignKey(
        Plan, verbose_name="Source", null=True, blank=True, unique=False,
        related_name="database_upgrades_source", on_delete=models.SET_NULL
    )
    source_plan_name = models.CharField(
        verbose_name="Source", max_length=100, null=True, blank=True
    )
    target_plan = models.ForeignKey(
        Plan, verbose_name="Target", null=True, blank=True, unique=False,
        related_name="database_upgrades_target", on_delete=models.SET_NULL
    )
    target_plan_name = models.CharField(
        verbose_name="Target", max_length=100, null=True, blank=True
    )

    def __unicode__(self):
        return "{} upgrade".format(self.database.name)

    def save(self, *args, **kwargs):
        if self.source_plan:
            self.source_plan_name = self.source_plan.name

        if self.target_plan:
            self.target_plan_name = self.target_plan.name

        super(DatabaseUpgrade, self).save(*args, **kwargs)


class DatabaseMigrateEngine(DatabaseUpgrade):

    current_database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="engine_migrations"
    )

    def __unicode__(self):
        return "{} migrate engine".format(self.database.name)


class DatabaseUpgradePatch(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="upgrades_patch"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_upgrades_patch"
    )
    source_patch = models.ForeignKey(
        EnginePatch, verbose_name="Source",
        null=True, blank=True, unique=False,
        related_name="database_minor_upgrades_source",
        on_delete=models.SET_NULL
    )
    source_patch_full_version = models.CharField(
        verbose_name="Source Patch", max_length=50, null=True, blank=True
    )
    target_patch = models.ForeignKey(
        EnginePatch, verbose_name="Target",
        null=True, blank=True, unique=False,
        related_name="database_minor_upgrades_target",
        on_delete=models.SET_NULL
    )
    target_patch_full_version = models.CharField(
        verbose_name="Target Patch", max_length=50, null=True, blank=True
    )

    def __unicode__(self):
        return "{} upgrade release".format(self.database.name)

    def save(self, *args, **kwargs):
        if self.source_patch:
            self.source_patch_full_version = self.source_patch.full_version

        if self.target_patch:
            self.target_patch_full_version = self.target_patch.full_version

        super(DatabaseUpgradePatch, self).save(*args, **kwargs)


class DatabaseReinstallVM(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="reinstall_vm"
    )
    instance = models.ForeignKey(
        Instance, verbose_name="Instance", null=False, unique=False,
        related_name="database_reinstall_vm"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_reinsgtall_vm"
    )

    def __unicode__(self):
        return "{} change parameters".format(self.database.name)


class DatabaseResize(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="resizes"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_resizes"
    )
    source_offer = models.ForeignKey(
        Offering, verbose_name="Source", null=True, blank=True,
        unique=False, related_name="database_resizes_source",
        on_delete=models.SET_NULL
    )
    source_offer_name = models.CharField(
        verbose_name="Source", max_length=100, null=True, blank=True
    )
    target_offer = models.ForeignKey(
        Offering, verbose_name="Target", null=True, blank=True,
        unique=False, related_name="database_resizes_target",
        on_delete=models.SET_NULL
    )
    target_offer_name = models.CharField(
        verbose_name="Target", max_length=100, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.source_offer:
            self.source_offer_name = self.source_offer.name

        if self.target_offer:
            self.target_offer_name = self.target_offer.name

        super(DatabaseResize, self).save(*args, **kwargs)

    def __unicode__(self):
        return "{} resize".format(self.database.name)


class DatabaseChangeParameter(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="change_parameters"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_change_parameters"
    )

    def __unicode__(self):
        return "{} change parameters".format(self.database.name)


class DatabaseCreate(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="create_database"
    )
    database = models.ForeignKey(
        Database, related_name='databases_create', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    infra = models.ForeignKey(DatabaseInfra, related_name='databases_create')
    plan = models.ForeignKey(
        Plan, null=True, blank=True,
        related_name='databases_create', on_delete=models.SET_NULL
    )
    plan_name = models.CharField(
        verbose_name="Plan", max_length=100, null=True, blank=True
    )
    environment = models.ForeignKey(
        Environment, related_name='databases_create'
    )
    team = models.ForeignKey(Team, related_name='databases_create')
    project = models.ForeignKey(
        Project, related_name='databases_create', null=True, blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    subscribe_to_email_events = models.BooleanField(default=True)
    is_protected = models.BooleanField(default=False)
    user = models.CharField(max_length=200)

    def __unicode__(self):
        return "Creating {}".format(self.name)

    @property
    def disable_retry_filter(self):
        return {'infra': self.infra}

    def update_step(self, step):
        if self.id:
            maintenance = self.__class__.objects.get(id=self.id)
            self.database = maintenance.database

        super(DatabaseCreate, self).update_step(step)

    def save(self, *args, **kwargs):
        if self.plan:
            self.plan_name = self.plan.name

        super(DatabaseCreate, self).save(*args, **kwargs)


class DatabaseClone(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="create_clone"
    )
    database = models.ForeignKey(
        Database, related_name='databases_clone', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    origin_database = models.ForeignKey(
        Database, related_name='origin_databases_clone', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    infra = models.ForeignKey(DatabaseInfra, related_name='databases_clone')
    plan = models.ForeignKey(
        Plan, null=True, blank=True,
        related_name='databases_clone', on_delete=models.SET_NULL
    )
    environment = models.ForeignKey(
        Environment, related_name='databases_clone'
    )
    name = models.CharField(max_length=200)
    user = models.CharField(max_length=200)

    def __unicode__(self):
        return "Cloning {}".format(self.origin_database.name)

    @property
    def disable_retry_filter(self):
        return {'infra': self.infra}

    def update_step(self, step):
        if self.id:
            maintenance = self.__class__.objects.get(id=self.id)
            self.database = maintenance.database

        super(DatabaseClone, self).update_step(step)


class DatabaseDestroy(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="databases_destroy"
    )
    database = models.ForeignKey(
        Database, related_name='databases_destroy', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    infra = models.ForeignKey(DatabaseInfra, related_name='databases_destroy')
    plan = models.ForeignKey(
        Plan, null=True, blank=True,
        related_name='databases_destroy', on_delete=models.SET_NULL
    )
    plan_name = models.CharField(
        verbose_name="Plan", max_length=100, null=True, blank=True
    )
    environment = models.ForeignKey(
        Environment, related_name='databases_destroy'
    )
    team = models.ForeignKey(Team, related_name='databases_destroy')
    project = models.ForeignKey(
        Project, related_name='databases_destroy', null=True, blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    subscribe_to_email_events = models.BooleanField(default=True)
    is_protected = models.BooleanField(default=False)
    user = models.CharField(max_length=200)

    def __unicode__(self):
        return "Destroying {}".format(self.name)

    @property
    def disable_retry_filter(self):
        return {'infra': self.infra}

    def update_step(self, step):
        if self.id:
            maintenance = self.__class__.objects.get(id=self.id)
            self.database = maintenance.database

        super(DatabaseDestroy, self).update_step(step)

    def save(self, *args, **kwargs):
        if self.plan:
            self.plan_name = self.plan.name

        super(DatabaseDestroy, self).save(*args, **kwargs)


class DatabaseRestore(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database", related_name="database_restore"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        related_name="database_restore"
    )
    group = models.ForeignKey(
        BackupGroup, verbose_name="Snapshot Group",
        related_name="database_restore"
    )
    new_group = models.ForeignKey(
        BackupGroup, verbose_name="Snapshot Group generated",
        null=True, blank=True, related_name="database_restore_new"
    )

    def __unicode__(self):
        return "{} change restore to {}".format(self.database, self.group)

    def load_instances(self, retry_from=None):
        if retry_from:
            self.__instance_retry(retry_from)
        else:
            self.__instances_groups()

    def __instance_retry(self, retry_from):
        for group in retry_from.restore_instances.all():
            instance = DatabaseRestoreInstancePair()
            instance.master = group.master
            instance.slave = group.slave
            instance.restore = self
            instance.save()

    def __instances_groups(self):
        driver = self.database.infra.get_driver()
        pairs = {}
        for instance in self.database.infra.instances.all():
            if not instance.is_database:
                continue

            if driver.check_instance_is_master(instance):
                master = instance
                slave = None
            else:
                master = driver.get_master_for(instance)
                slave = instance

            if not master:
                continue

            if master not in pairs:
                pairs[master] = []

            if slave:
                pairs[master].append(slave)

        for master, slaves in pairs.items():
            if slaves:
                for slave in slaves:
                    self.__add_instance(master, slave)
            else:
                self.__add_instance(master, master)

    def __add_instance(self, master, slave):
        instance = DatabaseRestoreInstancePair()
        instance.master = master
        instance.slave = slave
        instance.restore = self
        instance.save()

    def instances_pairs(self):
        return self.restore_instances.all().order_by('master')

    @property
    def instances(self):
        instances = []
        for pairs in self.instances_pairs():
            if pairs.master not in instances:
                instances.append(pairs.master)

            if pairs.slave not in instances:
                instances.append(pairs.slave)

        for instance in self.database.infra.instances.all():
            if instance.instance_type == instance.MONGODB_ARBITER:
                instances.append(instance)

        return instances

    def master_for(self, instance):
        for pair in self.instances_pairs():
            if pair.master == instance or pair.slave == instance:
                return pair.master

        raise DatabaseRestoreInstancePair.DoesNotExist(
            'No master for {}'.format(instance)
        )

    def is_master(self, instance):
        for pair in self.instances_pairs():
            if pair.master == instance:
                return True

        return False

    def is_slave(self, instance):
        for pair in self.instances_pairs():
            if pair.slave == instance:
                return True

        return False


class DatabaseRestoreInstancePair(BaseModel):

    master = models.ForeignKey(
        Instance, verbose_name="Master", related_name="restore_master"
    )
    slave = models.ForeignKey(
        Instance, verbose_name="Slave", related_name="restore_slave"
    )
    restore = models.ForeignKey(
        DatabaseRestore, verbose_name="Restore",
        related_name="restore_instances"
    )

    def __unicode__(self):
        return "{}: {} -> {}".format(self.restore, self.master, self.slave)

    class Meta:
        unique_together = (('master', 'slave', 'restore'), )


class DatabaseConfigureSSL(DatabaseMaintenanceTask):
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="configure_ssl"
    )
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="database_configure_ssl"
    )

    def __unicode__(self):
        return "{} Configure SSL".format(self.database.name)


class DatabaseMigrate(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="database_migrate"
    )
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="database_migrate"
    )
    environment = models.ForeignKey(
        Environment, null=False, related_name="database_migrate"
    )
    origin_environment = models.ForeignKey(Environment, null=False)
    offering = models.ForeignKey(
        Offering, related_name="database_migrate", null=True, blank=True
    )
    origin_offering = models.ForeignKey(Offering, null=True, blank=True)

    @property
    def host_migrate_snapshot(self):
        for host_migrate in self.hosts.all():
            if host_migrate.snapshot:
                return host_migrate.snapshot
        return

    def update_step(self, step):
        super(DatabaseMigrate, self).update_step(step)
        for host in self.hosts.all():
            host.update_step(step)

    def update_final_status(self, status):
        super(DatabaseMigrate, self).update_final_status(status)
        for host in self.hosts.all():
            host.update_final_status(status)
            host.can_do_retry = False
            host.save()

    @property
    def hosts_zones(self):
        hosts = {}
        for host in self.hosts.all():
            hosts[host.host] = host.zone
        return hosts

    def __unicode__(self):
        return "Migrate {} to {}".format(self.database, self.environment)


class HostMigrate(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="host_migrate"
    )
    host = models.ForeignKey(
        Host, null=False, related_name="migrate"
    )
    environment = models.ForeignKey(
        Environment, null=False, related_name="host_migrate"
    )
    zone = models.CharField(max_length=50, null=False)
    database_migrate = models.ForeignKey(
        DatabaseMigrate, null=True, blank=True, related_name="hosts"
    )
    snapshot = models.ForeignKey(
        Snapshot, null=True, blank=True, related_name="snapshot_migrate"
    )

    def __unicode__(self):
        return "Migrate {} to {}".format(self.host, self.zone)

    @property
    def disable_retry_filter(self):
        return {'host': self.host}

    def update_step(self, step):
        current_data = self._meta.model.objects.get(pk=self.id)
        self.host = current_data.host
        super(HostMigrate, self).update_step(step)


class RecreateSlave(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="recreate_slave"
    )
    host = models.ForeignKey(
        Host, null=False, related_name="recreate_slave"
    )
    snapshot = models.ForeignKey(
        Snapshot, null=True, blank=True, related_name="snapshot_recreate_slave"
    )

    def __unicode__(self):
        return "Recreate slave {}".format(self.host)

    @property
    def disable_retry_filter(self):
        return {'host': self.host}

    def update_step(self, step):
        current_data = self._meta.model.objects.get(pk=self.id)
        self.host = current_data.host
        super(RecreateSlave, self).update_step(step)


class FilerMigrate(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="filer_migrate"
    )
    original_export_id = models.CharField(max_length=200, null=False)
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="filer_migrate"
    )

    def __unicode__(self):
        return "Migrate filer"


class UpdateSsl(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="update_ssl_manager"
    )
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False, related_name="update_ssl_manager"
    )

    def __unicode__(self):
        return "Update SSL for {}".format(self.database)

    def cleanup(self, instances):
        from workflow.steps.util.db_monitor import EnableMonitoring
        from workflow.steps.util.zabbix import EnableAlarms
        extra_steps = (EnableMonitoring, EnableAlarms,)
        for step in extra_steps:
            for instance in instances:
                try:
                    step(instance).do()
                except Exception:
                    pass


class AddInstancesToDatabase(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, related_name="add_instances_to_database_manager"
    )
    database = models.ForeignKey(
        Database, verbose_name="Database",
        null=False, unique=False,
        related_name="add_instances_to_database_manager"
    )
    number_of_instances = models.PositiveIntegerField(
        verbose_name="Number of Instances", null=False, unique=False
    )
    number_of_instances_before = models.PositiveIntegerField(
        verbose_name="Number of Instances Before", null=True, unique=False
    )

    def __unicode__(self):
        return "Add instances to database: {}".format(self.database)


class RestartDatabase(DatabaseMaintenanceTask):
    task = models.ForeignKey(
        TaskHistory, verbose_name="Task History",
        null=False, unique=False, related_name="restart_database_manager"
    )
    database = models.ForeignKey(
        Database, related_name='restart_database_manager', null=True,
        blank=True, on_delete=models.SET_NULL
    )

    def __unicode__(self):
        return "Restarting database"


simple_audit.register(Maintenance)
simple_audit.register(HostMaintenance)
simple_audit.register(MaintenanceParameters)
simple_audit.register(DatabaseUpgrade)
simple_audit.register(DatabaseResize)
simple_audit.register(DatabaseChangeParameter)
simple_audit.register(DatabaseConfigureSSL)
simple_audit.register(HostMigrate)
simple_audit.register(DatabaseMigrate)
simple_audit.register(DatabaseUpgradePatch)
simple_audit.register(TaskSchedule)
simple_audit.register(RestartDatabase)


#########################################################
#                       SIGNALS                         #
#########################################################


@receiver(pre_delete, sender=Maintenance)
def maintenance_pre_delete(sender, **kwargs):
    """
    maintenance pre delete signal. Revoke scheduled task and remove
    its HostMaintenance objects
    """
    maintenance = kwargs.get("instance")
    LOG.debug("maintenance pre-delete triggered")
    HostMaintenance.objects.filter().delete()
    control.revoke(task_id=maintenance.celery_task_id)


@receiver(post_save, sender=Maintenance)
def maintenance_post_save(sender, **kwargs):
    """
     maintenance post save signal. Creates the maintenance
     task on celery and its HostMaintenance objetcs.
    """
    maintenance = kwargs.get("instance")
    is_new = kwargs.get("created")
    LOG.debug("maintenance post-save triggered")

    if is_new or not maintenance.celery_task_id:
        LOG.info("Spawning task and HostMaintenance objects...")

        if maintenance.save_host_maintenance():
            if maintenance.scheduled_for > datetime.now():
                task = execute_scheduled_maintenance.apply_async(
                    args=[maintenance.id],
                    eta=maintenance.scheduled_for.replace(
                        tzinfo=tz.tzlocal()
                    ).astimezone(tz.tzutc())
                )
            else:
                task = execute_scheduled_maintenance.apply_async(
                    args=[maintenance.id], countdown=5
                )

            maintenance.celery_task_id = task.task_id
            maintenance.save()
