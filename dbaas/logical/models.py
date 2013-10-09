# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField
from util import slugify
from util.models import BaseModel
from physical.models import Instance


class Product(BaseModel):

    name = models.CharField(verbose_name=_("Product name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is product active"), default=True)
    slug = models.SlugField()

    def __unicode__(self):
        return "%s" % self.name


class Database(BaseModel):

    RESERVED_DATABASES_NAME = ('admin', 'config', 'local')

    name = models.CharField(verbose_name=_("Database name"), max_length=100, unique=True)
    instance = models.ForeignKey(Instance, related_name="databases", on_delete=models.PROTECT)
    product = models.ForeignKey(Product, related_name="databases", on_delete=models.PROTECT)

    def __unicode__(self):
        return u"%s" % self.name

    def clean(self):

        if self.name in self.__get_database_reserved_names():
            raise ValidationError(_("%s is a reserved database name" % self.name))

    def __get_database_reserved_names(self):
        return Database.RESERVED_DATABASES_NAME


class Credential(BaseModel):
    user = models.CharField(verbose_name=_("User name"), max_length=100, unique=True)
    password = EncryptedCharField(verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey(Database, related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user


@receiver(pre_save, sender=Database)
def database_pre_save(sender, **kwargs):
    instance = kwargs.get('instance')
    
    #slugify name
    instance.name = slugify(instance.name)
    
    if instance.id:
        saved_object = Database.objects.get(id=instance.id)
        if instance.name != saved_object.name:
            raise AttributeError(_("Attribute name cannot be edited"))


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



simple_audit.register(Product, Database, Credential)
