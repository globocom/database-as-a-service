# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import simple_audit
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from .helper import slugify

LOG = logging.getLogger(__name__)


class BaseModel(models.Model):
    """Base model class"""

    created_at = models.DateTimeField(verbose_name=_("created_at"), auto_now_add=True, default=datetime.now())
    updated_at = models.DateTimeField(verbose_name=_("updated_at"), auto_now=True, default=datetime.now())

    class Meta:
        abstract = True


class Environment(BaseModel):

    name = models.CharField(verbose_name=_("Environment name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is environment active"), default=True)

    def __unicode__(self):
        return u"%s" % self.name


class Node(BaseModel):

    VIRTUAL = '1'
    PHYSICAL = '2'
    HOST_TYPE_CHOICES = (
        (VIRTUAL, 'Virtual Machine'),
        (PHYSICAL, 'Physical Node'),
    )

    address = models.CharField(verbose_name=_("Node address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Node port"))
    environment = models.ForeignKey('Environment', related_name="nodes", on_delete=models.PROTECT)
    is_active = models.BooleanField(verbose_name=_("Is node active"), default=True)
    type = models.CharField(verbose_name=_("Node type"),
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)


    class Meta:
        unique_together = (
            ('address', 'port', )
        )

    def __unicode__(self):
        return u"%s" % self.connection

    @property
    def connection(self):
        return u"%s:%s" % (self.address, self.port)


class EngineType(BaseModel):

    name = models.CharField(verbose_name=_("Engine name"), max_length=100, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


class Engine(BaseModel):

    version = models.CharField(verbose_name=_("Engine version"), max_length=100,)
    path = models.CharField(verbose_name=_("Engine path"), 
                            max_length=255, 
                            blank=True, 
                            null=True,
                            help_text=_("Path to look for the engine's executable file."))
    engine_type = models.ForeignKey("EngineType", verbose_name=_("Engine types"), related_name="engines", on_delete=models.PROTECT)

    class Meta:
        unique_together = (
            ('version', 'engine_type', )
        )

    def __unicode__(self):
        return u"%s_%s" % (self.engine_type.name, self.version)


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
    password = models.CharField(verbose_name=_("Instance password"), max_length=255, blank=True, null=False)
    node = models.OneToOneField("Node", on_delete=models.PROTECT)
    engine = models.ForeignKey("Engine", related_name="instances", on_delete=models.PROTECT)
    product = models.ForeignKey("business.Product", related_name="instances", null=True, blank=True, on_delete=models.PROTECT)
    plan = models.ForeignKey("business.Plan", related_name="instances", on_delete=models.PROTECT)

    def __unicode__(self):
        return self.name

    @property
    def engine_name(self):
        return self.engine.engine_type.name

    def clean(self, *args, **kwargs):
        LOG.debug('Checking instance status...')
        try:
            from base.engine import DriverFactory, GenericDriverError, ConnectionError, AuthenticationError
            engine = DriverFactory.factory(self)
            engine.check_status()
            LOG.debug('Instance %s is ok', self)
        except AuthenticationError, e:
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            raise ValidationError({'node': e.message})
        except GenericDriverError, e:
            raise ValidationError(e.message)


class Database(BaseModel):

    RESERVED_DATABASES_NAME = ('admin', 'config', 'local')

    name = models.CharField(verbose_name=_("Database name"), max_length=100, unique=True)
    instance = models.ForeignKey('Instance', related_name="databases", on_delete=models.PROTECT)

    def __unicode__(self):
        return u"%s" % self.name

    def clean(self):

        if self.name in self.__get_database_reserved_names():
            raise ValidationError(_("%s is a reserved database name" % self.name))

    def __get_database_reserved_names(self):
        return Database.RESERVED_DATABASES_NAME


@receiver(pre_save, sender=Database)
def database_pre_save(sender, **kwargs):
    instance = kwargs.get('instance')
    
    #slugify name
    instance.name = slugify(instance.name)
    
    if instance.id:
        saved_object = Database.objects.get(id=instance.id)
        if instance.name != saved_object.name:
            raise AttributeError(_("Attribute name cannot be edited"))


class Credential(BaseModel):
    user = models.CharField(verbose_name=_("User name"), max_length=100, unique=True)
    password = models.CharField(verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey('Database', related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user


@receiver(pre_save, sender=Credential)
def credential_pre_save(sender, **kwargs):
    instance = kwargs.get('instance')
    
    #slugify user
    instance.user = slugify(instance.user)
    
    if instance.id:
        saved_object = Credential.objects.get(id=instance.id)
        if instance.user != saved_object.user:
            raise AttributeError(_("Attribute user cannot be edited"))

        if instance.database != saved_object.database:
            raise AttributeError(_("Attribute database cannot be edited"))

simple_audit.register(Node, Environment, Instance, Database, Credential)
