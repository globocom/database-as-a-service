# coding=utf-8
import simple_audit
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

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

    address = models.CharField(verbose_name=_("Node address"), max_length=200, unique=True)
    port = models.IntegerField(verbose_name=_("Node port"))
    environment = models.ForeignKey('Environment', related_name="nodes")
    is_active = models.BooleanField(verbose_name=_("Is node active"), default=True)
    type = models.CharField(verbose_name=_("Node type"),
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)

    def __unicode__(self):
        return u"%s" % self.fqdn


class Environment(BaseModel):

    name = models.CharField(verbose_name=_("Environment name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is environment active"), default=True)

    def __unicode__(self):
        return u"%s" % self.name


class Instance(BaseModel):

    name = models.CharField(verbose_name=_("Instance name"), max_length=100, unique=True)
    user = models.CharField(verbose_name=_("Instance user"), max_length=100)
    password = models.CharField(verbose_name=_("Instance password"), max_length=255)
    node = models.OneToOneField("Node",)
    product = models.ForeignKey("business.Product", related_name="instances")
    plan = models.ForeignKey("business.Plan", related_name="instances")

    def uri(self):
        return 'mongodb://%s:%s' % (self.name, self.port)
    
    def __unicode__(self):
        return u"%s" % self.name


class Database(BaseModel):
    name = models.CharField(verbose_name=_("Database name"), max_length=100, unique=True)
    instance = models.ForeignKey('Instance', related_name="databases")

    def __unicode__(self):
        return u"%s" % self.name


class Credential(BaseModel):
    user = models.CharField(verbose_name=_("User name"), max_length=100, unique=True)
    password = models.CharField(verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey('Database', related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user


simple_audit.register(Node, Environment, Instance, Database, Credential)
