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
    is_active = models.BooleanField(verbose_name=_("host_is_active"), default=True)
    type = models.CharField(verbose_name=_("host_type"), 
                            max_length=2,
                            choices=HOST_TYPE_CHOICES,
                            default=PHYSICAL)

    def __unicode__(self):
        return u"%s" % self.fqdn

class Instance(BaseModel):
    
    name = models.CharField(verbose_name=_("instance_name"), max_length=100, unique=True)
    user = models.CharField(verbose_name=_("instance_user"), max_length=100, unique=True)
    port = models.IntegerField(verbose_name=_("instance_port"))
    password = models.CharField(verbose_name=_("instance_password"), max_length=255)
    host = models.OneToOneField(Host,)

    def uri(self):
        return 'mongodb://%s:%s' % (self.name, self.port)
    
    def __unicode__(self):
        return u"%s" % self.name
    
