# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
import datetime
import urllib
from datetime import date, timedelta
from django.db import models, transaction, Error
from django.db.models.signals import pre_save, post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField

from util import slugify, make_db_random_password
from util.models import BaseModel
from physical.models import DatabaseInfra, Environment, Offering
from drivers import factory_for
from system.models import Configuration
from account.models import Team
from drivers.base import DatabaseStatus
from drivers.errors import ConnectionError
from logical.validators import database_name_evironment_constraint
from workflow.steps.util.zabbix import DisableAlarms, EnableAlarms
from workflow.steps.util.db_monitor import DisableMonitoring, EnableMonitoring
from notification.models import TaskHistory
from util import get_credentials_for
from util import get_or_none_credentials_for
from dbaas_credentials.models import CredentialType
from system.models import Configuration
from django.utils.module_loading import import_by_path

LOG = logging.getLogger(__name__)
KB_FACTOR = 1.0 / 1024.0
MB_FACTOR = 1.0 / 1024.0 / 1024.0
GB_FACTOR = 1.0 / 1024.0 / 1024.0 / 1024.0


class Project(BaseModel):
    name = models.CharField(
        verbose_name=_("Project name"), max_length=100, unique=True)
    description = models.TextField(
        verbose_name=_("Description"), null=True, blank=True)
    is_active = models.BooleanField(
        verbose_name=_("Is project active"), default=True)
    slug = models.SlugField()

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        permissions = (
            ("view_project", "Can view projects"),
        )
        ordering = ['name']


class DatabaseAliveManager(models.Manager):

    def get_query_set(self):
        return Database.objects.filter(is_in_quarantine=False)


class DatabaseHistory(models.Model):
    database_id = models.IntegerField(db_index=True)
    environment = models.CharField(
        verbose_name=_("environment"), max_length=20
    )
    engine = models.CharField(
        verbose_name=_("engine"), max_length=100
    )
    name = models.CharField(
        verbose_name=_("name"), max_length=200
    )
    project = models.CharField(
        verbose_name=_("project"), max_length=100
    )
    team = models.CharField(
        verbose_name=_("team"), max_length=100
    )
    databaseinfra_name = models.CharField(
        verbose_name=_("databaseinfra_name"), max_length=100
    )
    plan = models.CharField(
        verbose_name=_("plan"), max_length=100
    )
    disk_size_kb = models.PositiveIntegerField(verbose_name=_("Size KB"))
    has_persistence = models.BooleanField(
        verbose_name="Disk persistence", default=True
    )

    created_at = models.DateTimeField(
        verbose_name=_("created_at"))
    deleted_at = models.DateTimeField(
        verbose_name=_("deleted_at"), auto_now_add=True)
    description = models.TextField(
        verbose_name=_("Description"), null=True, blank=True
    )


class Database(BaseModel):
    DEAD = 0
    ALIVE = 1
    INITIALIZING = 2
    ALERT = 3

    DB_STATUS = (
        (DEAD, 'Dead'),
        (ALIVE, 'Alive'),
        (INITIALIZING, 'Initializing'),
        (ALERT, 'Alert')
    )

    name = models.CharField(
        verbose_name=_("Database name"), max_length=100, db_index=True
    )
    databaseinfra = models.ForeignKey(
        DatabaseInfra, related_name="databases", on_delete=models.PROTECT
    )
    project = models.ForeignKey(
        Project, related_name="databases", on_delete=models.PROTECT, null=True, blank=True
    )
    team = models.ForeignKey(
        Team, related_name="databases", null=True, blank=True, help_text=_("Team that is accountable for the database")
    )
    is_in_quarantine = models.BooleanField(
        verbose_name=_("Is database in quarantine?"), default=False
    )
    is_monitoring = models.BooleanField(
        verbose_name=_("Is database being monitored?"), default=True
    )
    was_manually_stopped = models.BooleanField(
        verbose_name=_("The database was manually stoppped?"), default=False
    )
    attention = models.BooleanField(
        verbose_name=_("The database has GCP divergences?"), default=False, blank=True
    )
    attention_description = models.TextField(
        verbose_name=_("Database GCP divergences descriptions."), default="", null=True, blank=True
    )
    quarantine_dt = models.DateField(
        verbose_name=_("Quarantine date"), null=True, blank=True, editable=False
    )
    description = models.TextField(
        verbose_name=_("Description"), null=True, blank=True
    )
    status = models.IntegerField(choices=DB_STATUS, default=2)
    used_size_in_bytes = models.FloatField(default=0.0)
    environment = models.ForeignKey(
        Environment, related_name="databases", on_delete=models.PROTECT, db_index=True
    )
    backup_path = models.CharField(
        verbose_name=_("Backup path"), max_length=300, null=True, blank=True,
        help_text=_("Full path to backup file")
    )
    subscribe_to_email_events = models.BooleanField(
        verbose_name=_("Subscribe to email events"), default=True,
        help_text=_(
            "Check this box if you'd like to receive information "
            "regarding this database by email."
        )
    )
    disk_auto_resize = models.BooleanField(
        verbose_name=_("Disk auto resize"), default=True,
        help_text=_("When marked, the disk will be resized automatically.")
    )
    is_protected = models.BooleanField(
        verbose_name=_("Protected"), default=False, help_text=_("When marked, the database can not be deleted.")
    )
    quarantine_user = models.ForeignKey(
        User, related_name='databases_quarantine', null=True, blank=True, editable=False
    )
    apps_bind_name = models.TextField(
        verbose_name=_("apps_bind_name"), null=True, blank=True
    )
    send_all_chg = models.BooleanField(
        verbose_name=_("Send all changes to Service Now"), default=False, blank=True
    )
    can_do_autoupgrade = models.BooleanField(
        verbose_name=_("Allowed to AutoUpgrade its CPU/RAM Offer"), default=False
    )

    def validate_unique(self, *args, **kwargs):
        ''' Validate if database name is unique
            in environemnt stage'''
        super(Database, self).validate_unique(*args, **kwargs)

        if not any([
         hasattr(self, "environment"),
         hasattr(self, "name")]) or self.id:
            return

        environment = Environment.objects.filter(pk=self.environment_id)
        if not environment.exists():
            return
        environment = environment[0]
        db_check = Database.objects.filter(
            name=self.name,
            environment__stage=environment.stage
        )
        if db_check.exists():
            raise ValidationError({
                "name": [
                    "Name %s is alredy been used in the %s environment" % (
                        self.name,
                        Environment.get_stage_by_id(self.environment.stage)
                    )
                ]
            })

    def team_contact(self):
        if self.team:
            return self.team.emergency_contacts
    team_contact.short_description = 'Emergency contacts'

    objects = models.Manager()
    alive = DatabaseAliveManager()
    quarantine_time = Configuration.get_by_name_as_int(
        'quarantine_retention_days'
    )

    def __unicode__(self):
        return u"{}".format(self.name)

    class Meta:
        permissions = (
            ("can_manage_quarantine_databases",
             "Can manage databases in quarantine"),
            ("view_database", "Can view databases"),
            ("upgrade_mongo24_to_30",
             "Can upgrade mongoDB version from 2.4 to 3.0"),
            ("upgrade_database", "Can upgrade databases"),
            ("configure_ssl", "Can configure SSL"),
        )
        unique_together = (
            ('name', 'environment'),
        )

        ordering = ('name', )

    @property
    def is_in_memory(self):
        return self.engine.engine_type.is_in_memory

    @property
    def has_persistence(self):
        return self.plan.has_persistence

    @property
    def has_persistense_equivalent_plan(self):
        if self.plan.persistense_equivalent_plan:
            return True
        return False

    @property
    def persistence_change_text(self):
        if self.has_persistence:
            return 'Change to Memory Only'
        return 'Change to Persisted'

    @property
    def infra(self):
        return self.databaseinfra

    @property
    def engine_type(self):
        return self.infra.engine_name

    @property
    def engine(self):
        return self.infra.engine

    @property
    def plan(self):
        return self.databaseinfra and self.databaseinfra.plan

    @property
    def has_cost_credential(self):
        return get_or_none_credentials_for(
            self.infra.environment,
            CredentialType.GCP_COST
        )

    @property
    def gcp_log_credential(self):
        return get_or_none_credentials_for(
            self.environment,
            CredentialType.GCP_LOG
        )

    def pin_task(self, task):
        try:
            with transaction.atomic():
                DatabaseLock(database=self, task=task).save()
        except Error as e:
            LOG.error(e)
            return False
        else:
            return True

    @staticmethod
    def __clean_task(task_name):
        if task_name.endswith('_rollback'):
            return task_name.rsplit('_rollback', 1)[0]
        if task_name.endswith('_retry'):
            return task_name.rsplit('_retry', 1)[0]
        return task_name

    def update_task(self, task):
        lock = self.lock.first()
        if not lock:
            return self.pin_task(task)

        with transaction.atomic():
            lock = DatabaseLock.objects.select_for_update().filter(
                database=self
            ).first()

            task_name = self.__clean_task(task.task_name)
            if '.' in task_name:
                task_name = task_name.split('.')[-1]

            lock_task_name = self.__clean_task(lock.task.task_name)
            if '.' in lock_task_name:
                lock_task_name = lock_task_name.split('.')[-1]

            if lock_task_name != task_name or not lock.task.is_status_error:
                return False

            lock.task = task
            lock.save()
            return True

    def finish_task(self):
        for instance in self.infra.instances.all():
            try:
                instance.update_status()
            except Exception as e:
                LOG.error(
                    "Could not refresh status for {} - {}".format(instance, e)
                )
                continue

        try:
            self.update_status()
        except Exception as e:
            LOG.error("Could not refresh status for {} - {}".format(self, e))

        self.unpin_task()

    def update_status(self):
        self.status = Database.DEAD

        if self.database_status and self.database_status.is_alive:
            self.status = Database.ALIVE

            instances_status = self.databaseinfra.check_instances_status()
            if instances_status == self.databaseinfra.ALERT:
                self.status = Database.ALERT

        self.save(update_fields=['status'])

    def unpin_task(self):
        DatabaseLock.objects.filter(database=self).delete()

    @property
    def current_locked_task(self):
        lock = self.lock.first()
        if lock:
            return lock.task

    @property
    def is_locked(self):
        lock = self.lock.first()
        if lock:
            return True
        return False

    def delete(self, *args, **kwargs):
        if self.is_in_quarantine:
            LOG.warning(
                "Database {} is in quarantine and will be removed".format(
                    self.name
                )
            )
            for credential in self.credentials.all():
                instance = factory_for(self.databaseinfra)
                instance.try_remove_user(credential)

            engine = self.databaseinfra.engine
            databaseinfra = self.databaseinfra

            try:
                DatabaseHistory.objects.create(
                    database_id=self.id,
                    name=self.name,
                    description=self.description,
                    engine='{} {}'.format(
                        engine.engine_type.name,
                        engine.version
                    ),
                    project=self.project.name if self.project else '',
                    team=self.team.name if self.team else '',
                    databaseinfra_name=databaseinfra.name,
                    plan=databaseinfra.plan.name,
                    disk_size_kb=databaseinfra.disk_offering.size_kb,
                    has_persistence=databaseinfra.plan.has_persistence,
                    environment=self.environment.name,
                    created_at=self.created_at
                )
            except Exception as err:
                LOG.error(
                    ('Error on creating database history for '
                     '"database {}: {}'.format(self.id, err)))

            super(Database, self).delete(*args, **kwargs)

        else:
            LOG.warning("Putting database {} in quarantine".format(self.name))
            self.is_in_quarantine = True
            self.is_protected = False

            self.save()
            if self.credentials.exists():
                for credential in self.credentials.all():
                    new_password = make_db_random_password()
                    new_credential = Credential.objects.get(pk=credential.id)
                    new_credential.password = new_password
                    new_credential.save()

                    instance = factory_for(self.databaseinfra)
                    instance.try_update_user(new_credential)
            # Add step to stop database

    def clean(self):
        if not self.pk:
            self.name = slugify(self.name)

        if self.name in self.__get_database_reserved_names():
            raise ValidationError(
                _("{} is a reserved database name".format(
                    self.name
                ))
            )

    def automatic_create_first_credential(self):
        LOG.info("creating new credential for database {}".format(self.name))
        user = Credential.USER_PATTERN % self.name
        credential = Credential.create_new_credential(user, self)
        return credential

    @classmethod
    def provision(cls, name, databaseinfra):
        if not isinstance(databaseinfra, DatabaseInfra):
            raise ValidationError(
                'Invalid databaseinfra type {} - {}'.format(
                    type(databaseinfra), databaseinfra
                )
            )

        database = Database()
        database.databaseinfra = databaseinfra
        database.environment = databaseinfra.environment
        database.name = name
        database.full_clean()
        database.save()
        database = Database.objects.get(pk=database.pk)
        return database

    def __get_database_reserved_names(self):
        return getattr(self.driver, 'RESERVED_DATABASES_NAME', [])

    @property
    def driver(self):
        if self.databaseinfra_id is not None:
            return self.databaseinfra.get_driver()

    def get_endpoint(self):
        return self.driver.get_connection(database=self)

    def get_endpoint_dns(self):
        return self.driver.get_connection_dns(database=self)

    def get_endpoint_dns_simple(self):
        return self.driver.get_connection_dns_simple(database=self)

    def __kibana_url(self):
        if self.databaseinfra.plan.is_pre_provisioned:
            return ""

        credential = get_credentials_for(
            environment=self.environment,
            credential_type=CredentialType.KIBANA_LOG
        )
        search_field = credential.get_parameter_by_name('search_field')
        if not search_field:
            return ""
        time_query = "_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-6h,to:now))"
        filter_query = "_a=(columns:!(_source),filters:!(),interval:auto,query:(language:lucene,query:'{}:{}'))".format(
            search_field, self.name
        )
        return "{}/app/kibana#/discover?{}&{}".format(
            credential.endpoint, time_query, filter_query
        )

    def __gcp_log_url(self):
        from workflow.steps.util.base import HostProviderClient
        host_prov_client = HostProviderClient(self.environment)

        credential = self.gcp_log_credential

        vm_ids = host_prov_client.get_vm_ids(self.infra)

        search_filter = " OR ".join(
            ['resource.labels.instance_id="%s"' %
             x for x in vm_ids])
        new_filter = '(resource.type="gce_instance") AND ({})'.format(search_filter)
        query = "query;query=%(search_filter)s;" % {
            "search_filter": urllib.quote(new_filter)
        }

        project = "?project={}".format(credential.get_parameter_by_name("project"))

        url = "{endpoint}/logs/{query}{project}".format(
            endpoint=credential.endpoint,
            query=query,
            project=project
        )
        print('URL:', url)

        return url

    def get_log_url(self):
        if self.gcp_log_credential:
            return self.__gcp_log_url()
        else:
            return self.__kibana_url()

    def __activate_monitoring(self, instances):
        for instance in instances:
            EnableAlarms(instance).do()
            EnableMonitoring(instance).do()
        return

    def __deactivate_monitoring(self,instances):
        for instance in instances:
            DisableAlarms(instance).do()
            DisableMonitoring(instance).do()
        return

    def toggle_monitoring(self):
        instances = self.infra.get_driver().get_database_instances()
        if not self.is_monitoring:
            self.__activate_monitoring(instances)
        else:
            self.__deactivate_monitoring(instances)

    def get_chg_register_url(self):
        endpoint = Configuration.get_by_name('chg_register_url')
        url = "{endpoint}/chg_register/{database_name}".format(
            endpoint=endpoint,
            database_name=self.name
        )
        print('URL:', url)
        return url

    def get_dex_url(self):
        if Configuration.get_by_name_as_int('dex_analyze') != 1:
            return ""

        if self.databaseinfra.plan.is_pre_provisioned:
            return ""

        if self.engine_type != 'mongodb':
            return ""

        return 1

    def get_is_preprovisioned(self):
        return self.databaseinfra.plan.is_pre_provisioned

    endpoint = property(get_endpoint)
    endpoint_dns = property(get_endpoint_dns)

    @cached_property
    def database_status(self):
        try:
            info = self.databaseinfra.get_info()
            if info is None:
                return None
            database_status = info.get_database_status(self.name)

            if database_status is None:
                # try get without cache
                info = self.databaseinfra.get_info(force_refresh=True)
                database_status = info.get_database_status(self.name)
        except ConnectionError as e:
            msg = ("ConnectionError calling database_status for database {}:"
                   "{}").format(self, e)
            LOG.error(msg)
            database_status = DatabaseStatus(self)

        return database_status

    def get_offering_name(self):
        LOG.info("Get offering")
        try:
            offer_name = self.infra.offering.name
        except Exception as e:
            LOG.info("Oops...{}".format(e))
            offer_name = None

        return offer_name

    offering = property(get_offering_name)

    @property
    def total_size(self):
        return self.driver.masters_total_size_in_bytes

    @property
    def total_size_in_kb(self):
        return round(self.driver.masters_total_size_in_bytes * KB_FACTOR, 2)

    @property
    def total_size_in_mb(self):
        return round(self.driver.masters_total_size_in_bytes * MB_FACTOR, 2)

    @property
    def total_size_in_gb(self):
        return round(self.driver.masters_total_size_in_bytes * GB_FACTOR, 2)

    @property
    def used_size_in_kb(self):
        return self.driver.masters_used_size_in_bytes * KB_FACTOR

    @property
    def used_size_in_mb(self):
        return self.driver.masters_used_size_in_bytes * MB_FACTOR

    @property
    def used_size_in_gb(self):
        return self.driver.masters_used_size_in_bytes * GB_FACTOR

    @property
    def capacity(self):
        if self.status:
            return round(((1.0 * self.used_size_in_bytes / self.total_size) if self.total_size else 0, 2))

    @classmethod
    def purge_quarantine(self):
        quarantine_time = Configuration.get_by_name_as_int(
            'quarantine_retention_days')
        quarantine_time_dt = date.today() - timedelta(days=quarantine_time)
        databases = Database.objects.filter(
            is_in_quarantine=True, quarantine_dt__lte=quarantine_time_dt
        )
        for database in databases:
            database.delete()
            LOG.info(
                ("The database %s was deleted, because it was set to "
                 "quarentine %d days ago") % (database.name, quarantine_time)
            )

    @classmethod
    def clone(cls, database, clone_name, plan, environment, user):
        from notification.tasks import TaskRegister

        TaskRegister.database_clone(
            origin_database=database, clone_name=clone_name, plan=plan,
            environment=environment, user=user
        )

    @classmethod
    def restore(cls, database, snapshot, user):
        from notification.tasks import TaskRegister

        LOG.info(
            ("Changing database volume with params: "
             "database {} snapshot: {}, user: {}").format(
                database, snapshot, user
            )
        )
        TaskRegister.restore_snapshot(
            database=database, snapshot=snapshot, user=user
        )

    @classmethod
    def upgrade_disk_type(cls, database, disk_offering_type, user):
        from notification.tasks import TaskRegister

        LOG.info(
            ("Changing database volume with params: "
             "database {}, new_disk_type: {}, user: {}").format(
                database, disk_offering_type, user
            )
        )
        TaskRegister.upgrade_disk_type(
            database=database, new_disk_type_upgrade=disk_offering_type, user=user
        )

    @classmethod
    def start_database_vm(cls, database, user):
        from notification.tasks import TaskRegister

        LOG.info("Starting database with params: database {}, user: {}".format(database, user))

        TaskRegister.start_database_vm(
            database=database, user=user
        )

    @classmethod
    def stop_database_vm(cls, database, user):
        from notification.tasks import TaskRegister

        LOG.info("Starting database with params: database {}, user: {}".format(database, user))

        TaskRegister.stop_database_vm(
            database=database, user=user
        )

    @classmethod
    def resize(cls, database, offering, user):
        from notification.tasks import TaskRegister

        TaskRegister.database_resize(
            database=database, user=user,
            offering=offering
        )

#    @classmethod
#    def recover_snapshot(cls, database, snapshot, user, task_history):
#        from backup.tasks import restore_snapshot
#
#        restore_snapshot.delay(
#            database=database, snapshot=snapshot, user=user,
#            task_history=task_history
#        )

    def get_metrics_url(self):
        return "/admin/logical/database/{}/metrics/".format(self.id)

    def get_resize_retry_url(self):
        return "/admin/logical/database/{}/resize_retry/".format(self.id)

    def get_resize_rollback_url(self):
        return "/admin/logical/database/{}/resize_rollback/".format(self.id)

    def get_disk_resize_url(self):
        return "/admin/logical/database/{}/disk_resize/".format(self.id)

    def get_add_instances_database_retry_url(self):
        return "/admin/logical/database/{}/add_instances_database_retry/".format(self.id)

    def get_add_instances_database_rollback_url(self):
        return "/admin/logical/database/{}/add_instances_database_rollback/".format(self.id)

    def get_remove_instance_database_retry_url(self):
        return "/admin/logical/database/{}/remove_instance_database_retry/".format(self.id)

    def get_mongodb_engine_version_upgrade_url(self):
        return ("/admin/logical/database/{}/"
                "mongodb_engine_version_upgrade/").format(self.id)

    def get_upgrade_url(self):
        return "/admin/logical/database/{}/upgrade/".format(self.id)

    def get_upgrade_retry_url(self):
        return "/admin/logical/database/{}/upgrade_retry/".format(self.id)

    def get_migrate_engine_retry_url(self):
        return "/admin/logical/database/{}/migrate_engine_retry/".format(self.id)

    def get_upgrade_patch_url(self):
        return "/admin/logical/database/{}/upgrade_patch/".format(self.id)

    def get_upgrade_patch_retry_url(self):
        return "/admin/logical/database/{}/upgrade_patch_retry/".format(
            self.id
        )

    def get_change_parameters_retry_url(self):
        return "/admin/logical/database/{}/change_parameters_retry/".format(
            self.id
        )

    def get_reinstallvm_retry_url(self):
        return "/admin/logical/database/{}/reinstallvm_retry/".format(self.id)

    def get_recreateslave_retry_url(self):
        return "/admin/logical/database/{}/recreateslave_retry/".format(
            self.id
        )

    def get_configure_ssl_url(self):
        return "/admin/logical/database/{}/configure_ssl/".format(self.id)

    def get_configure_ssl_retry_url(self):
        return "/admin/logical/database/{}/configure_ssl_retry/".format(
            self.id
        )

    def get_set_ssl_required_url(self):
        return "/admin/logical/database/{}/set_ssl_required/".format(self.id)

    def get_set_ssl_required_retry_url(self):
        return "/admin/logical/database/{}/set_ssl_required_retry/".format(
            self.id
        )

    def get_set_ssl_not_required_url(self):
        return "/admin/logical/database/{}/set_ssl_not_required/".format(
            self.id)

    def get_set_ssl_not_required_retry_url(self):
        return "/admin/logical/database/{}/set_ssl_not_required_retry/".format(
            self.id
        )

    def get_change_persistence_url(self):
        return "/admin/logical/database/{}/change_persistence/".format(self.id)

    def get_change_persistence_retry_url(self):
        return "/admin/logical/database/{}/change_persistence_retry/".format(
            self.id
        )

    def is_mongodb_24(self):
        engine = self.engine
        if engine.name == 'mongodb' and engine.version.startswith('2.4'):
            return True
        return False

    def get_offering_id(self):
        LOG.info("Get offering")
        try:
            offer_id = self.infra.plan.stronger_offering.id
        except Exception as e:
            LOG.info("Oops...{}".format(e))
            offer_id = None

        return offer_id

    offering_id = property(get_offering_id)

    def is_being_used_elsewhere(self, skip_tasks=None):
        tasks = TaskHistory.objects.filter(
            task_status=TaskHistory.STATUS_WAITING,
            object_id=self.id,
            object_class=self._meta.db_table)

        if tasks:
            return True
        if not self.current_locked_task:
            return False

        skip_tasks = skip_tasks or []
        if self.current_locked_task.task_name in skip_tasks:
            if self.current_locked_task.is_status_error:
                return False

        return True

    def restore_allowed(self):
        if Configuration.get_by_name_as_int('restore_allowed') == 1:
            return True

        return False

    def has_offerings(self):
        offerings = self.environment.offerings.exclude(id=self.offering_id)

        return bool(offerings)

    def has_disk_offerings(self):
        from physical.models import DiskOffering

        offerings = DiskOffering.objects.exclude(
            id=self.databaseinfra.disk_offering.id
        )
        return bool(offerings)

    @property
    def can_modify_parameters(self):
        if self.plan.replication_topology.parameter.all():
            return True
        else:
            return False

    @property
    def is_host_migrate_available(self):
        from util.providers import get_host_migrate_steps
        class_path = self.plan.replication_topology.class_path
        try:
            get_host_migrate_steps(class_path)
        except NotImplementedError:
            return False
        else:
            return True

    @property
    def is_dead(self):
        if self.status != Database.ALIVE:
            return True

        if self.database_status and not self.database_status.is_alive:
            return True

        return False

    @property
    def is_alive(self):
        if self.status == Database.ALIVE:
            return True

        if self.database_status and self.database_status.is_alive:
            return True

        return False

    @classmethod
    def disk_resize(cls, database, new_disk_offering, user):
        from physical.models import DiskOffering
        from notification.tasks import TaskRegister

        disk_offering = DiskOffering.objects.get(id=new_disk_offering)

        TaskRegister.database_disk_resize(
            database=database, user=user, disk_offering=disk_offering
        )

    def update_host_disk_used_size(self, host_address, used_size_kb, total_size_kb=None):
        instance = self.databaseinfra.instances.filter(
            address=host_address
        ).first()
        if not instance:
            raise ObjectDoesNotExist()

        volume = instance.hostname.volumes.last()
        if not volume:
            return None

        if total_size_kb:
            volume.total_size_kb = total_size_kb

        volume.used_size_kb = used_size_kb
        volume.save(update_fields=['total_size_kb','used_size_kb'])
        return volume

    def can_be_cloned(self, database_view_button=False):
        if not self.plan.has_persistence:
            return False, "Database does not have persistence cannot be cloned"

        if self.is_being_used_elsewhere():
            return False, "Database is being used by another task"

        if self.is_in_quarantine:
            return False, "Database in quarantine cannot be cloned"

        if database_view_button:
            if self.status != self.ALIVE:
                return False, "Database is not alive and cannot be cloned"
        else:
            if self.is_dead:
                return False, "Database is not alive and cannot be cloned"

        return True, None

    def can_be_restored(self):
        if not self.restore_allowed():
            return False, ('Restore is not allowed. Please, contact DBaaS '
                           'team for more information')

        if self.is_in_quarantine:
            return False, "Database in quarantine cannot be restored"

        if self.status != self.ALIVE or self.is_dead:
            return False, "Database is not alive and cannot be restored"

        if self.is_being_used_elsewhere():
            return False, ("Database is being used by another task, please "
                           "check your tasks")

        return True, None

    def can_be_disk_type_upgraded(self):
        if self.is_in_quarantine:
            return False, "Database in quarantine cannot be upgraded"

        if self.status != self.ALIVE or self.is_dead:
            return False, "Database is not alive and cannot be upgraded"

        if self.is_being_used_elsewhere():
            return False, ("Database is being used by another task, please "
                           "check your tasks")

        return True, None

    def can_be_start_database_vm(self):
        if self.status != self.DEAD:
            return False, "Database is not dead and cannot be started"
        if self.is_being_used_elsewhere():
            return False, ("Database is being used by another task, please "
                           "check your tasks")
        return True, None

    def can_be_stop_database_vm(self):
        if self.status != self.ALIVE and self.is_dead:
            return False, "Database is not alive and cannot be stoped"
        if self.is_being_used_elsewhere():
            return False, ("Database is being used by another task, please "
                           "check your tasks")
        return True, None

    def can_be_deleted(self):
        error = None
        if self.is_protected and not self.is_in_quarantine:
            error = "Database {} is protected and cannot be deleted"
        # elif self.is_dead:
        #     error = "Database {} is not alive and cannot be deleted"
        # elif self.is_being_used_elsewhere():
        #     error = "Database {} cannot be deleted because" \
        #             " it is in use by another task."

        if error:
            return False, error.format(self.name)
        return True, None

    def can_do_upgrade_retry(self):
        error = None
        if self.is_mongodb_24():
            error = "MongoDB 2.4 cannot be upgraded by this task."
        elif self.is_in_quarantine:
            error = "Database in quarantine and cannot be upgraded."
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.upgrade_database')]):
            error = "Database cannot be upgraded because " \
                    "it is in use by another task."
        elif not self.infra.plan.engine_equivalent_plan:
            error = "Source plan do not has equivalent plan to upgrade."

        if error:
            return False, error
        return True, None

    def can_do_upgrade(self):
        can_do_upgrade, error = self.can_do_upgrade_retry()

        if can_do_upgrade:
            if self.is_dead:
                error = "Database is dead and cannot be upgraded."
            elif self.is_being_used_elsewhere():
                error = "Database cannot be upgraded because " \
                        "it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_engine_migration(self, retry=False):
        error = None

        if self.is_in_quarantine:
            error = "Database in quarantine and cannot be upgraded."
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.migrate_engine')]):
            error = "Database engine cannot be migrated because " \
                    "it is in use by another task."
        elif not retry and self.is_dead:
            error = "Database is dead and cannot be upgraded."
        elif not retry and self.is_being_used_elsewhere():
            error = "Database engine cannot be migrated because " \
                    "it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_upgrade_patch_retry(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot be upgraded."
        elif self.is_being_used_elsewhere(
            ['notification.tasks.upgrade_database_patch']
        ):
            error = "Database cannot be upgraded because " \
                    "it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_upgrade_patch(self):
        can_do_upgrade, error = self.can_do_upgrade_patch_retry()

        if can_do_upgrade:
            if self.is_dead:
                error = "Database is dead and cannot be upgraded."
            elif self.is_being_used_elsewhere():
                error = "Database cannot be upgraded because " \
                        "it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_resize_retry(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot be resized."
        elif not self.has_offerings:
            error = "There is no offerings for this database."
        elif self.is_being_used_elsewhere(['notification.tasks.resize_database', 'notification.tasks.resize_database_rollback']):
            error = "Database cannot be resized because" \
                    " it is in use by another task."
        if error:
            return False, error
        return True, None

    def can_do_resize(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot be resized."
        elif not self.has_offerings:
            error = "There is no offerings for this database."
        elif self.is_dead:
            error = "Database is dead and cannot be resized."
        elif self.is_being_used_elsewhere():
            error = "Database cannot be resized because" \
                    " it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_change_parameters_retry(self):
        error = None
        if self.is_in_quarantine:
            error = ("Database in quarantine and cannot have the parameters "
                     "changed.")
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.change_parameters_database')]):
            error = "Database cannot have the parameters changed because" \
                    " it is in use by another task."
        if error:
            return False, error
        return True, None

    def can_do_change_parameters(self):
        error = None
        if self.is_in_quarantine:
            error = ("Database in quarantine and cannot have the parameters "
                     "changed.")
        elif self.is_dead:
            error = "Database is dead and cannot have the parameters changed."
        elif self.is_being_used_elsewhere():
            error = "Database cannot have the parameters changed because" \
                    " it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_migrate_host(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot have host migrate."
        elif self.is_dead:
            error = "Database is dead and cannot migrate host"
        elif self.is_being_used_elsewhere():
            error = ("Database cannot migrate host it is in use "
                     "by another task.")

        if error:
            return False, error
        return True, None

    def can_do_change_persistence_retry(self):
        error = None
        if self.is_in_quarantine:
            error = ("Database in quarantine and cannot have the persistence "
                     "changed.")
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.change_database_persistence')]):
            error = "Database cannot have the persistence changed because" \
                    " it is in use by another task."
        elif not self.has_persistense_equivalent_plan:
            error = "Database cannot have the persistence changed because" \
                    " it has not any persistense equivalent plan "

        if error:
            return False, error
        return True, None

    def can_do_change_persistence(self):
        error = None
        if self.is_in_quarantine:
            error = ("Database in quarantine and cannot have the persistence "
                     "changed.")
        elif self.is_dead:
            error = "Database is dead and cannot have the persistence changed."
        elif self.is_being_used_elsewhere():
            error = "Database cannot have the persistence changed because" \
                    " it is in use by another task."
        elif not self.has_persistense_equivalent_plan:
            error = "Database cannot have the persistence changed because" \
                    " it has not any persistense equivalent plan "

        if error:
            return False, error
        return True, None

    def can_do_disk_resize(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot be resized."
        elif self.is_being_used_elsewhere():
            error = "Database cannot be resized because" \
                    " it is in use by another task."
        elif not self.has_disk_offerings:
            error = "There is no other disk offering for this database."

        if error:
            return False, error
        return True, None

    def can_do_configure_ssl_retry(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot have SSL cofigured."
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.configure_ssl_database')]):
            error = "Database cannot have SSL cofigured because " \
                    "it is in use by another task."
        if error:
            return False, error
        return True, None

    def can_do_configure_ssl(self):
        can_do_configure_ssl, error = self.can_do_configure_ssl_retry()

        if can_do_configure_ssl:
            if self.is_dead:
                error = "Database is dead and cannot have SSL cofigured."
            elif self.is_being_used_elsewhere():
                error = "Database cannot have SSL cofigured because " \
                        "it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_set_ssl_required_retry(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot have set SSL " \
                    "required."
        elif self.is_being_used_elsewhere([('notification.tasks'
                                            '.database_set_ssl_required')]):
            error = "Database cannot have set SSL required " \
                    "because it is in use by another task."
        if error:
            return False, error
        return True, None

    def can_do_set_ssl_required(self):
        can_do_set_ssl_required, error = self.can_do_set_ssl_required_retry()

        if can_do_set_ssl_required:
            if self.is_dead:
                error = "Database is dead and cannot have set SSL required."
            elif self.is_being_used_elsewhere():
                error = "Database cannot have set SSL required " \
                        "because it is in use by another task."

        if error:
            return False, error
        return True, None

    def can_do_set_ssl_not_required_retry(self):
        error = None
        if self.is_in_quarantine:
            error = "Database in quarantine and cannot have set SSL not " \
                    "required."
        elif self.is_being_used_elsewhere(
            [('notification.tasks.database_set_ssl_not_required')]):
            error = "Database cannot have set SSL not required " \
                    "because it is in use by another task."
        if error:
            return False, error
        return True, None

    def can_do_set_ssl_not_required(self):
        can_do_ssl, error = self.can_do_set_ssl_not_required_retry()

        if can_do_ssl:
            if self.is_dead:
                error = "Database is dead and cannot have set SSL not " \
                        "required."
            elif self.is_being_used_elsewhere():
                error = "Database cannot have set SSL not required " \
                        "because it is in use by another task."

        if error:
            return False, error
        return True, None

    def destroy(self, user):
        if not self.is_in_quarantine:
            self.delete()
            return

        if self.plan.provider != self.plan.CLOUDSTACK:
            self.delete()
            return

        LOG.debug(
            "call destroy_database - name={}, team={}, project={}, "
            "user={}".format(self.name, self.team, self.project, user)
        )

        from notification.tasks import TaskRegister

        TaskRegister.database_destroy(database=self, user=user)
        return

    @property
    def last_successful_upgrade(self):
        from maintenance.models import DatabaseUpgrade
        return self.upgrades.filter(status=DatabaseUpgrade.SUCCESS).last()

    @property
    def status_html(self):
        html_default = '<span class="label label-{}">{}</span>'

        if self.status == Database.ALIVE:
            status = html_default.format("success", "Alive")
        elif self.status == Database.DEAD:
            status = html_default.format("important", "Dead")
        elif self.status == Database.ALERT:
            status = html_default.format("warning", "Alert")
        else:
            status = html_default.format("info", "Initializing")

        return format_html(status)

    @property
    def migrating_html(self):
        html_default = '&nbsp;<span class="label label-{}">{}</span>'

        if self.infra.migration_in_progress:
            status = html_default.format("info", "Migrating ({} of {})".format(
                self.infra.migration_stage, self.infra.total_stages_migration))
            return format_html(status)

        return ""

    @property
    def organization(self):
        return self.team.organization

    def update_team_labels(self):
        status = True
        host_provider_class = "workflow.steps.util.host_provider.UpdateTeamLabelsVmInstances"
        volume_provider_class = "workflow.steps.util.volume_provider.UpdateTeamLabelsDisks"
        step_class_host_provider = import_by_path(host_provider_class)
        step_class_volume_provider = import_by_path(volume_provider_class)
        try:
            instances = self.infra.instances.all()
            for i in instances:
                step_class_host_provider(i).do()
                step_class_volume_provider(i).do()
            msg = "Labels Updated successfully"
        except Exception as error:
            msg = ("Error to update team labels: {}".format(str(error)))
            LOG.error(msg)
            status = False
        return status, msg
    
    def get_future_offering(self, resize_target):
        LOG.info('Buscando Future Offering de %s para database %s -> Offer atual: %s', resize_target, self.name, self.infra.offering.name)
        current_offer = self.infra.offering
        environment = self.environment

        future_offer = None

        # Busca ofertas disponíveis para o environment
        possible_offerings_environment = self.get_possible_future_offerings_for_environment(environment)

        if resize_target == 'cpu':
            # Busca por offer > de CPU e >= de RAM
            future_offer = self.get_next_offer_for_cpu(environment, current_offer, possible_offerings_environment)

        elif resize_target == 'ram':
            # Busca por offer >= de CPU e > de RAM
            future_offer = self.get_next_offer_for_ram(environment, current_offer, possible_offerings_environment)
            
        elif resize_target == 'cpu_ram':
            # Busca por offer > de CPU e > de RAM
            future_offer = self.get_next_offer_for_cpu_ram(environment, current_offer, possible_offerings_environment)
            
        LOG.info('Future Offering selecionada: %s', future_offer.name)

        return future_offer
    
    def get_possible_future_offerings_for_environment(self, environment):
        # Busca na Configuration os nomes resumidos (ex: c2m2) das offerings disponíveis no DBaaS para auto upgrade
        possible_offerings_names = Configuration.get_by_name_as_list(
            'allowed_future_offerings_names_auto_upgrade_vm'
            )
        LOG.info('Possiveis offerings no DBaaS: %s', possible_offerings_names)
        
        possible_offerings_environment = []

        # traz o nome real das Offerings, ja filtrando pelo environment
        for possible_offer in possible_offerings_names:
            offer_with_name = environment.offerings.filter(name__icontains=possible_offer).first()
            if offer_with_name:
                possible_offerings_environment.append(offer_with_name.name)

        return possible_offerings_environment
    
    def get_next_offer_for_cpu(self, environment, current_offer, possible_offerings_environment):
        return environment.offerings.filter(
                cpus__gt=current_offer.cpus, 
                memory_size_mb__gte=current_offer.memory_size_mb,
                name__in=possible_offerings_environment).order_by('cpus', 'memory_size_mb').first()

    def get_next_offer_for_ram(self, environment, current_offer, possible_offerings_environment):
        return environment.offerings.filter(
            cpus__gte=current_offer.cpus, 
            memory_size_mb__gt=current_offer.memory_size_mb,
            name__in=possible_offerings_environment).order_by('cpus', 'memory_size_mb').first()

    def get_next_offer_for_cpu_ram(self, environment, current_offer, possible_offerings_environment):
        return environment.offerings.filter(
            cpus__gt=current_offer.cpus, 
            memory_size_mb__gt=current_offer.memory_size_mb,
            name__in=possible_offerings_environment).order_by('cpus', 'memory_size_mb').first()


class DatabaseLock(BaseModel):
    database = models.ForeignKey(
        Database, related_name="lock", unique=True
    )
    task = models.ForeignKey(
        TaskHistory, related_name="lock"
    )


class Credential(BaseModel):
    USER_PATTERN = "u_%s"
    USER_MAXIMUM_LENGTH_NAME = 16

    user = models.CharField(verbose_name=_("User name"), max_length=100)
    password = EncryptedCharField(
        verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey(Database, related_name="credentials")
    force_ssl = models.BooleanField(default=False)

    OWNER = 'Owner'
    READ_WRITE = 'Read-Write'
    READ_ONLY = 'Read-Only'

    PRIVILEGES_CHOICES = {
        (OWNER, 'Owner'),
        (READ_WRITE, 'Read-Write'),
        (READ_ONLY, 'Read-Only'),
    }

    privileges = models.CharField(max_length=10, choices=PRIVILEGES_CHOICES,
                                  default=OWNER)

    def __unicode__(self):
        return u"%s" % self.user

    class Meta:
        permissions = (
            ("view_credential", "Can view credentials"),
        )
        unique_together = (
            ('user', 'database'),
        )
        ordering = ('database', 'user',)

    def clean(self):
        if len(self.user) > self.USER_MAXIMUM_LENGTH_NAME:
            raise ValidationError(_("%s is too long" % self.user))

    @cached_property
    def driver(self):
        return self.database.databaseinfra.get_driver()

    def reset_password(self):
        """ Reset credential password to a new random password """
        self.password = make_db_random_password()
        self.driver.update_user(self)
        self.save()

    @property
    def ssl_swap_label(self):
        if self.force_ssl:
            return "Disable SSL"
        else:
            return "Enable SSL"

    def swap_force_ssl(self):
        if self.force_ssl:
            self.force_ssl = False
            self.driver.set_user_not_require_ssl(self)
            self.save()
        else:
            self.force_ssl = True
            self.driver.set_user_require_ssl(self)
            self.save()

    @classmethod
    def create_new_credential(cls, user, database, privileges="Owner"):
        credential = Credential()
        credential.database = database
        credential.user = user[:cls.USER_MAXIMUM_LENGTH_NAME]
        credential.user = slugify(credential.user)
        credential.password = make_db_random_password()
        credential.privileges = privileges
        credential.full_clean()
        credential.driver.create_user(credential)
        credential.save()
        return credential

    def delete(self, *args, **kwargs):
        self.driver.remove_user(self)
        LOG.info('User removed from driver')
        super(Credential, self).delete(*args, **kwargs)


#
# SIGNALS
#


@receiver(pre_delete, sender=Database)
def database_pre_delete(sender, **kwargs):
    """
database pre delete signal. Removes database from the engine
"""
    database = kwargs.get("instance")
    LOG.debug("database pre-delete triggered")
    engine = factory_for(database.databaseinfra)
    engine.try_remove_database(database)


@receiver(post_save, sender=Database, dispatch_uid="database_drive_credentials")
def database_post_save(sender, **kwargs):
    """
        Database post save signal. Creates the database in the driver and
        creates a new credential.
    """
    database = kwargs.get("instance")
    is_new = kwargs.get("created")
    LOG.debug("database post-save triggered")
    if is_new and database.engine_type != 'redis':
        LOG.info(
            ("a new database (%s) were created... "
             "provision it in the engine" % (
                database.name))
            )
        engine = factory_for(database.databaseinfra)
        engine.create_database(database)
        database.automatic_create_first_credential()


@receiver(pre_save, sender=Database)
def database_pre_save(sender, **kwargs):
    from notification.tasks import TaskRegister

    database = kwargs.get('instance')
    if database.is_in_quarantine:
        if database.quarantine_dt is None:
            database.quarantine_dt = datetime.datetime.now().date()

        if not database.quarantine_user:
            from dbaas.middleware import UserMiddleware
            database.quarantine_user = UserMiddleware.current_user()
    else:
        database.quarantine_dt = None
        database.quarantine_user = None

    if database.id:
        saved_object = Database.objects.get(id=database.id)
        if database.name != saved_object.name:
            raise AttributeError(_("Attribute name cannot be edited"))

        if database.team and saved_object.team:
            if database.team.organization != saved_object.team.organization:
                TaskRegister.update_organization_name_monitoring(
                    database=database,
                    organization_name=database.team.organization.name)
                if saved_object.team.external:
                    TaskRegister.update_database_monitoring(
                        database=database,
                        hostgroup=(saved_object.team.organization
                                   .grafana_hostgroup),
                        action='remove')
                if database.team.external:
                    TaskRegister.update_database_monitoring(
                        database=database,
                        hostgroup=database.team.organization.grafana_hostgroup,
                        action='add')

    else:
        # new database
        if database_name_evironment_constraint(
           database.name, database.environment.name):
            raise AttributeError(
                _('%s already exists in production!') % database.name
            )

        LOG.debug("slugfying database's name for %s" % database.name)
        database.name = slugify(database.name)


@receiver(pre_save, sender=Credential)
def credential_pre_save(sender, **kwargs):
    credential = kwargs.get('instance')

    if credential.id:
        saved_object = Credential.objects.get(id=credential.id)
        if credential.user != saved_object.user:
            raise AttributeError(_("Attribute user cannot be edited"))

        if credential.database != saved_object.database:
            raise AttributeError(_("Attribute database cannot be edited"))


@receiver(pre_save, sender=Project)
def project_pre_save(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.slug = slugify(instance.name)


class NoDatabaseInfraCapacity(Exception):

    """ There isn't databaseinfra capable to support a new database
        with this plan """
    pass


simple_audit.register(Project, Database, Credential)
