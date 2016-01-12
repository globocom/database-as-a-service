# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel
from drivers import DatabaseInfraStatus
from django.utils.functional import cached_property

LOG = logging.getLogger(__name__)


class Environment(BaseModel):
    name = models.CharField(
        verbose_name=_("Environment"), max_length=100, unique=True)
    equivalent_environment = models.ForeignKey(
        "Environment", null=True, blank=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return '%s' % (self.name)


class EngineType(BaseModel):

    name = models.CharField(
        verbose_name=_("Engine name"), max_length=100, unique=True)

    class Meta:
        permissions = (
            ("view_enginetype", "Can view engine types"),
        )

    def __unicode__(self):
        return "%s" % (self.name,)

    @property
    def default_plan(self):
        return Plan.objects.get(is_default=True, engine_type=self)


class Engine(BaseModel):

    engine_type = models.ForeignKey(EngineType, verbose_name=_(
        "Engine types"), related_name="engines", on_delete=models.PROTECT)
    version = models.CharField(
        verbose_name=_("Engine version"), max_length=100,)
    path = models.CharField(verbose_name=_("Engine path"),
                            max_length=255,
                            blank=True,
                            null=True,
                            help_text=_("Path to look for the engine's executable file."))
    template_name = models.CharField(verbose_name=_("Template Name"),
                                     max_length=200,
                                     blank=True,
                                     null=True,
                                     help_text="Template name registered in your provision system")
    user_data_script = models.TextField(verbose_name=_("User data script"),
                                        blank=True,
                                        null=True,
                                        help_text="Script that will be sent as an user-data to provision the virtual machine")
    engine_upgrade_option = models.ForeignKey("Engine", null=True, blank=True,
                                              verbose_name=_("Engine version upgrade"),
                                              on_delete=models.SET_NULL,
                                              related_name='backwards_engine')

    class Meta:
        unique_together = (
            ('version', 'engine_type', )
        )
        permissions = (
            ("view_engine", "Can view engines"),
        )

    @property
    def name(self):
        return self.engine_type.name

    def __unicode__(self):
        return "%s_%s" % (self.name, self.version)


class Plan(BaseModel):

    PREPROVISIONED = 0
    CLOUDSTACK = 1

    PROVIDER_CHOICES = (
        (PREPROVISIONED, 'Pre Provisioned'),
        (CLOUDSTACK, 'Cloud Stack'),
    )

    name = models.CharField(
        verbose_name=_("Plan name"), max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(
        verbose_name=_("Is plan active"), default=True)
    is_default = models.BooleanField(verbose_name=_("Is plan default"),
                                     default=False,
                                     help_text=_("Check this option if this the default plan. There can be only one..."))
    is_ha = models.BooleanField(verbose_name=_("Is plan HA"), default=False)
    engine = models.ForeignKey(Engine, verbose_name=_("Engine"),
                               related_name='plans')
    environments = models.ManyToManyField(Environment)
    provider = models.IntegerField(choices=PROVIDER_CHOICES,
                                   default=0)
    max_db_size = models.IntegerField(default=0,
                                      verbose_name=_("Max database size (MB)"),
                                      help_text=_("What is the maximum size of each database (MB). 0 means unlimited."))
    equivalent_plan = models.ForeignKey("Plan", null=True, blank=True,
                                        verbose_name=_("Region Migration plan"),
                                        on_delete=models.SET_NULL)
    engine_equivalent_plan = models.ForeignKey("Plan", null=True, blank=True,
                                               verbose_name=_("Engine version upgrade plan"),
                                               on_delete=models.SET_NULL,
                                               related_name='backwards_plan')

    @property
    def engine_type(self):
        return self.engine.engine_type

    @property
    def engines(self):
        return Engine.objects.filter(id=self.engine_id)

    def __unicode__(self):
        return "%s" % (self.name)

    def environment(self):
        return ', '.join([e.name for e in self.environments.all()])

    class Meta:
        permissions = (
            ("view_plan", "Can view plans"),
        )


class PlanAttribute(BaseModel):

    name = models.CharField(
        verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(
        verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey(Plan, related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)

    class Meta:
        permissions = (
            ("view_planattribute", "Can view plan attributes"),
        )


class DatabaseInfra(BaseModel):

    ALIVE = 1
    DEAD = 0
    ALERT = 2

    INFRA_STATUS = (
        (ALIVE, "Alive"),
        (DEAD, "Dead"),
        (ALERT, "Alert"))

    name = models.CharField(verbose_name=_("DatabaseInfra Name"),
                            max_length=100,
                            unique=True,
                            help_text=_("This could be the fqdn associated to the databaseinfra."))
    user = models.CharField(verbose_name=_("DatabaseInfra User"),
                            max_length=100,
                            help_text=_(
                                "Administrative user with permission to manage databases, create users and etc."),
                            blank=True,
                            null=False)
    password = EncryptedCharField(
        verbose_name=_("DatabaseInfra Password"), max_length=255, blank=True, null=False)
    engine = models.ForeignKey(
        Engine, related_name="databaseinfras", on_delete=models.PROTECT)
    plan = models.ForeignKey(
        Plan, related_name="databaseinfras", on_delete=models.PROTECT)
    environment = models.ForeignKey(
        Environment, related_name="databaseinfras", on_delete=models.PROTECT)
    capacity = models.PositiveIntegerField(
        default=1, help_text=_("How many databases is supported"))
    per_database_size_mbytes = models.IntegerField(default=0,
                                                   verbose_name=_(
                                                       "Max database size (MB)"),
                                                   help_text=_("What is the maximum size of each database (MB). 0 means unlimited."))
    endpoint = models.CharField(verbose_name=_("DatabaseInfra Endpoint"),
                                max_length=255,
                                help_text=_(
                                    "Usually it is in the form host:port[,host_n:port_n]. If the engine is mongodb this will be automatically generated."),
                                blank=True,
                                null=True)

    endpoint_dns = models.CharField(verbose_name=_("DatabaseInfra Endpoint (DNS)"),
                                    max_length=255,
                                    help_text=_(
                                        "Usually it is in the form host:port[,host_n:port_n]. If the engine is mongodb this will be automatically generated."),
                                    blank=True,
                                    null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ("view_databaseinfra", "Can view database infras"),
        )

    def clean(self, *args, **kwargs):
        if (not self.environment_id or not self.plan_id) or not self.plan.environments.filter(pk=self.environment_id).exists():
            raise ValidationError({'engine': _("Invalid environment")})

    @property
    def engine_name(self):
        if self.engine and self.engine.engine_type:
            return self.engine.engine_type.name
        return None

    @property
    def per_database_size_bytes(self):
        if not self.per_database_size_mbytes:
            return 0
        return self.per_database_size_mbytes * 1024 * 1024

    @property
    def used(self):
        """ How many databases is allocated in this datainfra """
        return self.databases.count()

    @property
    def available(self):
        """ How many databases still supports this datainfra.
        Returns
            0 if datainfra is full
            < 0 if datainfra is overcapacity
            > 0 if datainfra can support more databases
        """
        return self.capacity - self.used

    @classmethod
    def get_unique_databaseinfra_name(cls, base_name):
        """
        try diferent names if first exists, like NAME-1, NAME-2, ...
        """
        i = 0
        name = base_name
        while DatabaseInfra.objects.filter(name=name).exists():
            i += 1
            name = "%s-%d" % (base_name, i)
        LOG.info("databaseinfra unique name to be returned: %s" % name)
        return name

    @classmethod
    def get_active_for(cls, plan=None, environment=None):
        """Return active databaseinfras for selected plan and environment"""
        datainfras = DatabaseInfra.objects.filter(
            plan=plan, environment=environment, instances__is_active=True).distinct()
        LOG.debug('Total of datainfra with filter plan %s and environment %s: %s',
                  plan, environment, len(datainfras))
        return datainfras

    @classmethod
    def best_for(cls, plan, environment, name):
        """ Choose the best DatabaseInfra for another database """
        datainfras = list(
            DatabaseInfra.get_active_for(plan=plan, environment=environment))
        if not datainfras:
            return None
        datainfras.sort(key=lambda di: -di.available)
        best_datainfra = datainfras[0]
        if best_datainfra.available <= 0:
            return None
        return best_datainfra

    def check_instances_status(self):
        alive_instances = self.instances.filter(status=Instance.ALIVE).count()
        dead_instances = self.instances.filter(status=Instance.DEAD).count()

        if dead_instances == 0:
            status = self.ALIVE
        elif alive_instances == 0:
            status = self.DEAD
        else:
            status = self.ALERT

        return status

    def get_driver(self):
        import drivers
        return drivers.factory_for(self)

    def get_info(self, force_refresh=False):
        if not self.pk:
            return None
        key = "datainfra:info:%d" % self.pk
        info = None

        if not force_refresh:
            # try use cache
            info = cache.get(key)

        if info is None:
            try:
                info = self.get_driver().info()
                cache.set(key, info)
            except:
                # To make cache possible if the database hangs the connection
                # with no reply
                info = DatabaseInfraStatus(databaseinfra_model=self.__class__)
                info.databases_status[self.databases.all()[0].name] = DatabaseInfraStatus(
                    databaseinfra_model=self.__class__)
                info.databases_status[
                    self.databases.all()[0].name].is_alive = False

                cache.set(key, info)
        return info


class Host(BaseModel):
    hostname = models.CharField(
        verbose_name=_("Hostname"), max_length=255, unique=True)
    address = models.CharField(verbose_name=_("Host address"), max_length=255)
    monitor_url = models.URLField(
        verbose_name=_("Monitor Url"), max_length=500, blank=True, null=True)
    future_host = models.ForeignKey(
        "Host", null=True, blank=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.hostname

    class Meta:
        permissions = (
            ("view_host", "Can view hosts"),
        )


class Instance(BaseModel):

    DEAD = 0
    ALIVE = 1
    INITIALIZING = 2

    INFRA_STATUS = (
        (DEAD, 'Dead'),
        (ALIVE, 'Alive'),
        (INITIALIZING, 'Initializing')
    )

    NONE = 0
    MYSQL = 1
    MONGODB = 2
    MONGODB_ARBITER = 3
    REDIS = 4
    REDIS_SENTINEL = 5

    DATABASE_TYPE = (
        (NONE, 'None'),
        (MYSQL, 'MySQL'),
        (MONGODB, 'MongoDB'),
        (MONGODB_ARBITER, 'Arbiter'),
        (REDIS, 'Redis'),
        (REDIS_SENTINEL, 'Sentinel'),
    )

    dns = models.CharField(verbose_name=_("Instance dns"), max_length=200)
    address = models.CharField(
        verbose_name=_("Instance address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Instance port"))
    databaseinfra = models.ForeignKey(
        DatabaseInfra, related_name="instances", on_delete=models.CASCADE)
    is_active = models.BooleanField(
        verbose_name=_("Is instance active"), default=True)
    is_arbiter = models.BooleanField(
        verbose_name=_("Is arbiter"), default=False)
    hostname = models.ForeignKey(Host)
    status = models.IntegerField(choices=INFRA_STATUS, default=2)
    instance_type = models.IntegerField(choices=DATABASE_TYPE, default=0)
    future_instance = models.ForeignKey(
        "Instance", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = (
            ('address', 'port',)
        )
        permissions = (
            ("view_instance", "Can view instances"),
        )

    @property
    def connection(self):
        return "%s:%s" % (self.address, self.port)

    def __unicode__(self):
        return "%s:%s" % (self.dns, self.port)

    def clean(self, *args, **kwargs):
        if self.is_arbiter or not self.is_active:
            # no connection check is needed
            return

        LOG.debug('Checking instance %s (%s) status...',
                  self.connection, self.databaseinfra)
        # self.clean_fields()

        if not self.databaseinfra.engine_id:
            raise ValidationError({'engine': _("No engine selected")})

        from drivers import factory_for, GenericDriverError, ConnectionError, AuthenticationError
        try:
            engine = factory_for(self.databaseinfra)
            # validate instance connection before saving
            engine.check_status(instance=self)
            LOG.debug('Instance %s is ok', self)
        except AuthenticationError, e:
            LOG.exception(e)
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next
            # versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            LOG.exception(e)
            raise ValidationError({'instance': e.message})
        except GenericDriverError, e:
            LOG.exception(e)
            raise ValidationError(e.message)

    def check_status(self):
        try:
            status = self.databaseinfra.get_driver().check_status(
                instance=self)
            return status
        except Exception, e:
            return False


##########################################################################
# SIGNALS
##########################################################################

@receiver(pre_delete, sender=Instance)
def instance_pre_delete(sender, **kwargs):
    """
    instance pre delete
    """

    from backup.models import Snapshot
    import datetime

    instance = kwargs.get('instance')

    LOG.debug("instance %s pre-delete" % (instance))

    snapshots = Snapshot.objects.filter(
        instance=instance, purge_at__isnull=True)
    for snapshot in snapshots:
        LOG.debug("Setting snapshopt %s purge_at time" % (snapshot))
        snapshot.purge_at = datetime.datetime.now()
        snapshot.save()

    LOG.debug("instance pre-delete triggered")


@receiver(post_save, sender=DatabaseInfra)
def databaseinfra_post_save(sender, **kwargs):
    """
    databaseinfra post save
    """
    databaseinfra = kwargs.get('instance')
    LOG.debug("databaseinfra post-save triggered")
    LOG.debug("databaseinfra %s endpoint: %s" %
              (databaseinfra, databaseinfra.endpoint))


@receiver(pre_save, sender=DatabaseInfra)
def databaseinfra_pre_save(sender, **kwargs):
    """
    databaseinfra pre save
    """
    databaseinfra = kwargs.get('instance')
    LOG.debug("databaseinfra pre-save triggered")
    if not databaseinfra.plan:
        databaseinfra.plan = databaseinfra.engine.engine_type.default_plan
        LOG.warning("No plan specified, using default plan (%s) for engine %s" % (
            databaseinfra, databaseinfra.engine))


@receiver(pre_save, sender=Plan)
def plan_pre_save(sender, **kwargs):
    """
    plan pre save
    databaseinfra is a plan object and not an implementation from DatabaseInfra's model
    """

    plan = kwargs.get('instance')
    LOG.debug("plan pre-save triggered")
    if plan.is_default:
        LOG.debug(
            "looking for other plans marked as default (they will be marked as false) with engine type %s" % plan.engine_type)
        if plan.id:
            plans = Plan.objects.filter(
                is_default=True, engine=plan.engine).exclude(id=plan.id)
        else:
            plans = Plan.objects.filter(
                is_default=True, engine=plan.engine)
        if plans:
            with transaction.commit_on_success():
                for plan in plans:
                    LOG.info(
                        "marking plan %s(%s) attr is_default to False" % (plan, plan.engine_type))
                    plan.is_default = False
                    plan.save(update_fields=['is_default'])
        else:
            LOG.debug("No plan found")


simple_audit.register(
    EngineType, Engine, Plan, PlanAttribute, DatabaseInfra, Instance)
