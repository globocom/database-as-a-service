# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField
from util.models import BaseModel

LOG = logging.getLogger(__name__)


class EngineType(BaseModel):

    name = models.CharField(verbose_name=_("Engine name"), max_length=100, unique=True)

    def __unicode__(self):
        return self.name


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
    def node(self):
        # temporary
        return self.nodes.all()[0]

    @property
    def engine_name(self):
        return self.engine.engine_type.name


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


simple_audit.register(EngineType, Engine, Plan, PlanAttribute, Instance, Node)
