# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel


LOG = logging.getLogger(__name__)

class Environment(BaseModel):
    name = models.CharField(verbose_name=_("Environment"), max_length=100, unique=True)


class EngineType(BaseModel):

    name = models.CharField(verbose_name=_("Engine name"), max_length=100, unique=True)


    class Meta:
        permissions = (
            ("view_enginetype", "Can view engine types"),
        )

    @property
    def default_plan(self):
        return Plan.objects.get(is_default=True, engine_type=self)


class Engine(BaseModel):

    engine_type = models.ForeignKey(EngineType, verbose_name=_("Engine types"), related_name="engines", on_delete=models.PROTECT)
    version = models.CharField(verbose_name=_("Engine version"), max_length=100,)
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

    name = models.CharField(verbose_name=_("Plan name"), max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(verbose_name=_("Is plan active"), default=True)
    is_default = models.BooleanField(verbose_name=_("Is plan default"),
                                     default=False,
                                     help_text=_("Check this option if this the default plan. There can be only one..."))
    engine_type = models.ForeignKey(EngineType, verbose_name=_("Engine Type"), related_name='plans')
    environments = models.ManyToManyField(Environment)

    @property
    def engines(self):
        return Engine.objects.filter(engine_type_id=self.engine_type_id)


    class Meta:
        permissions = (
            ("view_plan", "Can view plans"),
        )


class PlanAttribute(BaseModel):

    name = models.CharField(verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey(Plan, related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)

    class Meta:
        permissions = (
            ("view_planattribute", "Can view plan attributes"),
        )

class DatabaseInfra(BaseModel):

    name = models.CharField(verbose_name=_("DatabaseInfra Name"),
                            max_length=100,
                            unique=True,
                            help_text=_("This could be the fqdn associated to the databaseinfra."))
    user = models.CharField(verbose_name=_("DatabaseInfra User"),
                            max_length=100,
                            help_text=_("Administrative user with permission to manage databases, create users and etc."),
                            blank=True,
                            null=False)
    password = EncryptedCharField(verbose_name=_("DatabaseInfra Password"), max_length=255, blank=True, null=False)
    engine = models.ForeignKey(Engine, related_name="databaseinfras", on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name="databaseinfras", on_delete=models.PROTECT)
    environment = models.ForeignKey(Environment, related_name="databaseinfras", on_delete=models.PROTECT)
    capacity = models.PositiveIntegerField(default=1, help_text=_("How many databases is supported"))
    per_database_size_mbytes = models.IntegerField(default=0, 
                                                    verbose_name=_("Max database size (MB)"), 
                                                    help_text=_("What is the maximum size of each database (MB). 0 means unlimited."))
    endpoint = models.CharField(verbose_name=_("DatabaseInfra Endpoint"),
                            max_length=255,
                            help_text=_("Usually it is in the form host:port[,host_n:port_n]. If the engine is mongodb this will be automatically generated."),
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
    def best_for(cls, plan, environment):
        """ Choose the best DatabaseInfra for another database """
        datainfras = list(DatabaseInfra.objects.filter(plan=plan, environment=environment))
        LOG.debug('Total of datainfra with filter plan %s and environment %s: %s', plan, environment, len(datainfras))
        if not datainfras:
            return None
        datainfras.sort(key=lambda di: -di.available)
        best_datainfra = datainfras[0]
        if best_datainfra.available <= 0:
            return None
        return best_datainfra

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
            info = self.get_driver().info()
            cache.set(key, info)
        return info


class Host(BaseModel):
    hostname = models.CharField(verbose_name=_("Hostname"), max_length=255, unique=True)
    monitor_url = models.URLField(verbose_name=_("Monitor Url"), max_length=500, blank=True, null=True)

    def __unicode__(self):
        return self.hostname

    class Meta:
        permissions = (
            ("view_host", "Can view hosts"),
        )


class Instance(BaseModel):

    address = models.CharField(verbose_name=_("Instance address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Instance port"))
    databaseinfra = models.ForeignKey(DatabaseInfra, related_name="instances", on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name=_("Is instance active"), default=True)
    is_arbiter = models.BooleanField(verbose_name=_("Is arbiter"), default=False)
    hostname = models.ForeignKey(Host)

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
        return self.connection

    def clean(self, *args, **kwargs):
        if self.is_arbiter or not self.is_active:
            # no connection check is needed
            return

        LOG.debug('Checking instance %s (%s) status...', self.connection, self.databaseinfra)
        # self.clean_fields()

        if not self.databaseinfra.engine_id:
            raise ValidationError({'engine': _("No engine selected")})

        from drivers import factory_for, GenericDriverError, ConnectionError, AuthenticationError
        try:
            engine = factory_for(self.databaseinfra)
            #validate instance connection before saving
            engine.check_status(instance=self)
            LOG.debug('Instance %s is ok', self)
        except AuthenticationError, e:
            LOG.exception(e)
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            LOG.exception(e)
            raise ValidationError({'instance': e.message})
        except GenericDriverError, e:
            LOG.exception(e)
            raise ValidationError(e.message)

#####################################################################################################
# SIGNALS
#####################################################################################################

@receiver(post_save, sender=DatabaseInfra)
def databaseinfra_post_save(sender, **kwargs):
    """
    databaseinfra post save
    """
    databaseinfra = kwargs.get('instance')
    LOG.debug("databaseinfra post-save triggered")
    LOG.debug("databaseinfra %s endpoint: %s" % (databaseinfra, databaseinfra.endpoint))

@receiver(pre_save, sender=DatabaseInfra)
def databaseinfra_pre_save(sender, **kwargs):
    """
    databaseinfra pre save
    """
    databaseinfra = kwargs.get('instance')
    LOG.debug("databaseinfra pre-save triggered")
    if not databaseinfra.plan:
        databaseinfra.plan = databaseinfra.engine.engine_type.default_plan
        LOG.warning("No plan specified, using default plan (%s) for engine %s" % (databaseinfra, databaseinfra.engine))


@receiver(pre_save, sender=Plan)
def plan_pre_save(sender, **kwargs):
    """
    plan pre save
    databaseinfra is a plan object and not an implementation from DatabaseInfra's model
    """

    plan = kwargs.get('instance')
    LOG.debug("plan pre-save triggered")
    if plan.is_default:
        LOG.debug("looking for other plans marked as default (they will be marked as false) with engine type %s" % plan.engine_type)
        if plan.id:
            plans = Plan.objects.filter(is_default=True, engine_type=plan.engine_type).exclude(id=plan.id)
        else:
            plans = Plan.objects.filter(is_default=True, engine_type=plan.engine_type)
        if plans:
            with transaction.commit_on_success():
                for plan in plans:
                    LOG.info("marking plan %s(%s) attr is_default to False" % (plan, plan.engine_type))
                    plan.is_default = False
                    plan.save(update_fields=['is_default'])
        else:
            LOG.debug("No plan found")


simple_audit.register(EngineType, Engine, Plan, PlanAttribute, DatabaseInfra, Instance)
