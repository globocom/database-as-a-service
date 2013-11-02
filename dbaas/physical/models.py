# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel


LOG = logging.getLogger(__name__)


class EngineType(BaseModel):

    name = models.CharField(verbose_name=_("Engine name"), max_length=100, unique=True)

    def __unicode__(self):
        return self.name

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

    @property
    def engines(self):
        return Engine.objects.filter(engine_type_id=self.engine_type_id)

    def __unicode__(self):
        return "%s" % self.name


class PlanAttribute(BaseModel):

    name = models.CharField(verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey(Plan, related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)


class DatabaseInfra(BaseModel):

    name = models.CharField(verbose_name=_("DatabaseInfra name"),
                            max_length=100,
                            unique=True,
                            help_text=_("This could be the fqdn associated to the databaseinfra."))
    user = models.CharField(verbose_name=_("DatabaseInfra user"),
                            max_length=100,
                            help_text=_("Administrative user with permission to manage databases, create users and etc."),
                            blank=True,
                            null=False)
    password = EncryptedCharField(verbose_name=_("DatabaseInfra password"), max_length=255, blank=True, null=False)
    engine = models.ForeignKey(Engine, related_name="databaseinfras", on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name="databaseinfras", on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name
        
    def env_variables(self, database_name=None):
        """
        Returns a dictionary with the variables to be exported in users environment

        Example: {
            "MYSQL_HOST":"10.10.10.10",
            "MYSQL_PORT":3306,
            "MYSQL_USER":"ROOT",
            "MYSQL_PASSWORD":"s3cr3t",
            "MYSQL_DATABASE_NAME":"myapp"
        }
        """
        from logical.models import Database, Credential
        # TODO: deal with multiple databases with the same name but associated with differente products
        try:
            database = Database.objects.get(name=database_name)
            credential = Credential.objects.get(database=database, user=Credential.USER_PATTERN % (database_name))
        except Credential.DoesNotExist:
            LOG.warning("Credential for database %s not found. Trying to create a new one..." % database_name)
            credential = database.create_new_credential()
        
        envs = {}
        prefix = self.engine.name.upper()
        envs["%s_HOST" % prefix] = "%s" % self.instance.address
        envs["%s_PORT" % prefix] = "%s" % self.instance.port
        envs["%s_USER" % prefix] = "%s" % credential.user
        envs["%s_PASSWORD" % prefix] = "%s" % credential.password
        envs["%s_DATABASE_NAME" % prefix] = "%s" % database.name

        return envs

    @property
    def instance(self):
        # temporary
        return self.instances.all()[0]

    @property
    def engine_name(self):
        if self.engine and self.engine.engine_type:
            return self.engine.engine_type.name
        return None

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
    def best_for(cls, plan):
        """ Choose the best DatabaseInfra for another database """
        # FIXME For a while, choose always first database
        databases = DatabaseInfra.objects.filter(plan=plan).all()
        if not databases:
            return None
        return databases[0]

    def get_driver(self):
        import drivers
        return drivers.factory_for(self)



class Host(BaseModel):
    hostname = models.CharField(verbose_name=_("Hostname"), max_length=255, unique=True)

    def __unicode__(self):
        return self.hostname


class Instance(BaseModel):

    VIRTUAL = '1'
    PHYSICAL = '2'
    HOST_TYPE_CHOICES = (
        (VIRTUAL, 'Virtual Machine'),
        (PHYSICAL, 'Physical Instance'),
    )

    address = models.CharField(verbose_name=_("Instance address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Instance port"))
    databaseinfra = models.ForeignKey(DatabaseInfra, related_name="instances", on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name=_("Is instance active"), default=True)
    is_arbiter = models.BooleanField(verbose_name=_("Is arbiter"), default=False)
    hostname = models.ForeignKey(Host)
    type = models.CharField(verbose_name=_("Instance type"),
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)

    class Meta:
        unique_together = (
            ('address', 'port',)
        )

    @property
    def connection(self):
        return "%s:%s" % (self.address, self.port)

    def __unicode__(self):
        return self.connection

    def clean(self, *args, **kwargs):
        LOG.debug('Checking instance %s (%s) status...', self.connection, self.databaseinfra)
        # self.clean_fields()

        if not self.databaseinfra.engine_id:
            raise ValidationError({'engine': _("No engine selected")})

        from drivers import factory_for, GenericDriverError, ConnectionError, AuthenticationError
        try:
            engine = factory_for(self.databaseinfra)
            engine.check_status(instance=self)
            LOG.debug('Instance %s is ok', self)
        except AuthenticationError, e:
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            raise ValidationError({'instance': e.message})
        except GenericDriverError, e:
            raise ValidationError(e.message)

#####################################################################################################
# SIGNALS
#####################################################################################################

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
