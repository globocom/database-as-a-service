# coding=utf-8
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _

class BaseModel(models.Model):
    """Base model class"""

    created_at = models.DateTimeField(verbose_name=_("created_at"), auto_now_add=True, default=datetime.now())
    updated_at = models.DateTimeField(verbose_name=_("updated_at"), auto_now=True, default=datetime.now())

    class Meta:
        abstract = True


class Host(BaseModel):

    VIRTUAL = '1'
    PHYSICAL = '2'
    HOST_TYPE_CHOICES = (
        (VIRTUAL, 'Virtual Machine'),
        (PHYSICAL, 'Physical Host'),
    )

    fqdn = models.CharField(verbose_name=_("host_fqdn"), max_length=200, unique=True)
    environment = models.ForeignKey('base.Environment', related_name="hosts")
    is_active = models.BooleanField(verbose_name=_("host_is_active"), default=True)
    type = models.CharField(verbose_name=_("host_type"),
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)

    def __unicode__(self):
        return u"%s" % self.fqdn


class Environment(BaseModel):

    name = models.CharField(verbose_name=_("environment_name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("environment_is_active"), default=True)

    def __unicode__(self):
        return u"%s" % self.name


class Instance(BaseModel):

    name = models.CharField(verbose_name=_("instance_name"), max_length=100, unique=True)
    user = models.CharField(verbose_name=_("instance_user"), max_length=100, unique=True)
    password = models.CharField(verbose_name=_("instance_password"), max_length=255)
    port = models.IntegerField(verbose_name=_("instance_port"))
    password = models.CharField(verbose_name=_("instance_password"), max_length=255)
    host = models.OneToOneField("base.Host",)
    product = models.ForeignKey("business.Product", related_name="instances")
    plan = models.ForeignKey("business.Plan", related_name="instances")

    def uri(self):
        return 'mongodb://%s:%s' % (self.name, self.port)
    
    def __unicode__(self):
        return u"%s" % self.name


class Database(BaseModel):
    name = models.CharField(verbose_name=_("database_name"), max_length=100, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


class Credential(BaseModel):
    user = models.CharField(verbose_name=_("credentials_user"), max_length=100, unique=True)
    password = models.CharField(verbose_name=_("credentials_password"), max_length=255)
    database = models.ForeignKey('base.Database', related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user

