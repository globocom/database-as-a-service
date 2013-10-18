# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf import settings
import time
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

    def __unicode__(self):
        return "%s_%s" % (self.engine_type.name, self.version)


class Plan(BaseModel):

    name = models.CharField(verbose_name=_("Plan name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is plan active"), default=True)
    is_default = models.BooleanField(verbose_name=_("Is plan default"), 
                                    default=False,
                                    help_text=_("Check this option if this the default plan. There can be only one..."))
    engine_type = models.ForeignKey(EngineType, verbose_name=_("Engine Type"), related_name='plans')

    def __unicode__(self):
        return "%s" % self.name


class PlanAttribute(BaseModel):

    name = models.CharField(verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey(Plan, related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)


class Instance(BaseModel):

    name = models.CharField(verbose_name=_("Instance name"), 
                            max_length=100, 
                            unique=True,
                            help_text=_("This could be the fqdn associated to the instance."))
    user = models.CharField(verbose_name=_("Instance user"), 
                            max_length=100,
                            help_text=_("Administrative user with permission to manage databases, create users and etc."),
                            blank=True, 
                            null=False)
    password = EncryptedCharField(verbose_name=_("Instance password"), max_length=255, blank=True, null=False)
    engine = models.ForeignKey(Engine, related_name="instances", on_delete=models.PROTECT)
    plan = models.ForeignKey(Plan, related_name="instances", on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name
    
    @property
    def env_variables(self):
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
        envs = {}
        prefix = self.engine.engine_type.name.upper()
        envs["%s_HOST" % prefix] = self.node.address
        envs["%s_PORT" % prefix] = self.node.port
        envs["%s_USER" % prefix] = self.user
        envs["%s_PASSWORD" % prefix] = self.password
        #For now, we can only have one database per instance
        envs["%s_DATABASE_NAME" % prefix] = self.name
        
        return envs
    @property
    def node(self):
        # temporary
        return self.nodes.all()[0]

    @property
    def engine_name(self):
        return self.engine.engine_type.name

    @classmethod
    def get_unique_instance_name(cls, base_name):
        """
        try diferent names if first exists, like NAME-1, NAME-2, ...
        """
        i = 0
        name=base_name
        while Instance.objects.filter(name=name).exists():
            i += 1
            name = "%s-%d" % (base_name, i)
        LOG.info("instance unique name to be returned: %s" % name)
        return name
    
    @classmethod
    def provision_database(cls, instance=None):
        from logical.models import Database
        from drivers import factory_for
        
        database = Database.objects.get_or_create(name=instance.name, instance=instance)
        # engine = factory_for(instance)
        # engine.create_database(database)

        return database
        
    @classmethod
    def provision(cls, engine=None, plan=None, name=None):
        # create new instance

        LOG.debug("provisioning instance with engine: %s | plan: %s | name: %s" % (engine, plan, name))

        instance = Instance()
        instance.name = Instance.get_unique_instance_name(name)
        instance.engine = engine
        instance.user = getattr(settings, "DB_DEFAULT_USER", "")
        instance.password = getattr(settings, "DB_DEFAULT_PASSWORD", "")
        #if plan is none, then default plan is set via signal.
        if plan:
            instance.plan = plan
        else:
            instance.plan = instance.engine.engine_type.default_plan
        instance.save()

        # now, create a node
        # hardcode!!!
        from providers import ProviderFactory
        provider = ProviderFactory.factory()
        node = provider.create_node(instance)

        from drivers import factory_for
        driver = factory_for(instance)
        max_retries = 15
        retry = 0
        while True:
            #TODO: timeout or use some async job
            # if retry == max_retries:
            #     raise Exception(_("Max retries (%d) reached when trying to create a node." % max_retries))
            time.sleep(10)
            try:
                LOG.debug('Waiting for node %s...', node)
                driver.check_status(node=node)
                break
            except:
                LOG.warning('Node %s not ready...', node, exc_info=True)
                retry += 1
        
        LOG.info('Retries until the node creation for instance %s: %s' % (instance, retry))
        node.is_active = True
        node.save()
        
        #returns the instance
        return instance


class Node(BaseModel):

    VIRTUAL = '1'
    PHYSICAL = '2'
    HOST_TYPE_CHOICES = (
        (VIRTUAL, 'Virtual Machine'),
        (PHYSICAL, 'Physical Node'),
    )

    address = models.CharField(verbose_name=_("Node address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Node port"))
    instance = models.ForeignKey(Instance, related_name="nodes", on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name=_("Is node active"), default=True)
    type = models.CharField(verbose_name=_("Node type"),
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)


    class Meta:
        unique_together = (
            ('address', 'port', )
        )

    @property
    def connection(self):
        return "%s:%s" % (self.address, self.port)

    def __unicode__(self):
        return self.connection

    def clean(self, *args, **kwargs):
        LOG.debug('Checking node %s (%s) status...', self.connection, self.instance)
        # self.clean_fields()
        from drivers import factory_for, GenericDriverError, ConnectionError, AuthenticationError
        try:
            engine = factory_for(self.instance)
            engine.check_status(node=self)
            LOG.debug('Node %s is ok', self)
        except AuthenticationError, e:
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            raise ValidationError({'node': e.message})
        except GenericDriverError, e:
            raise ValidationError(e.message)

#####################################################################################################
# SIGNALS
#####################################################################################################
@receiver(pre_save, sender=Instance)
def instance_pre_save(sender, **kwargs):
    """
    instance pre save
    """
    instance = kwargs.get('instance')
    LOG.debug("instance pre-save triggered")
    if not instance.plan:
        instance.plan = instance.engine.engine_type.default_plan
        LOG.warning("No plan specified, using default plan (%s) for engine %s" % (instance, instance.engine))

@receiver(pre_save, sender=Plan)
def plan_pre_save(sender, **kwargs):
    """
    plan pre save
    instance is a plan object and not an implementation from Instance's model
    """
    
    instance = kwargs.get('instance')
    LOG.debug("plan pre-save triggered")
    if instance.is_default:
        LOG.debug("looking for other plans marked as default (they will be marked as false) with engine type %s" % instance.engine_type)
        if instance.id:
            plans = Plan.objects.filter(is_default=True, engine_type=instance.engine_type).exclude(id=instance.id)
        else:
            plans = Plan.objects.filter(is_default=True, engine_type=instance.engine_type)
        if plans:
            with transaction.commit_on_success():
                for plan in plans:
                    LOG.info("marking plan %s(%s) attr is_default to False" % (plan, plan.engine_type))
                    plan.is_default=False
                    plan.save(update_fields=['is_default'])
        else:
            LOG.debug("No plan found")


simple_audit.register(EngineType, Engine, Plan, PlanAttribute, Instance, Node)
