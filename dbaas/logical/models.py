# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField
from util import slugify
from util.models import BaseModel
from physical.models import Instance
from drivers import factory_for

LOG = logging.getLogger(__name__)

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
    product = models.ForeignKey(Product, related_name="databases", on_delete=models.PROTECT, null=True, blank=True)

    def __unicode__(self):
        return u"%s" % self.name

    def clean(self):

        if self.name in self.__get_database_reserved_names():
            raise ValidationError(_("%s is a reserved database name" % self.name))

    def create_new_credential(self):
        """creates a new credential for the database with a random password"""
        engine = factory_for(self.instance)
        LOG.info("creating new credential for database %s" % self.name)
        credential = Credential(user=Credential.USER_PATTERN % self.name, password=engine.make_random_password(), database=self)
        credential.save()
        engine.create_user(credential)
        return credential
        
    def __get_database_reserved_names(self):
        return Database.RESERVED_DATABASES_NAME


class Credential(BaseModel):

    USER_PATTERN = "u_%s"

    user = models.CharField(verbose_name=_("User name"), max_length=100, unique=True)
    password = EncryptedCharField(verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey(Database, related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user


#####################################################################################################
# SIGNALS
#####################################################################################################
@receiver(pre_delete, sender=Database)
def database_pre_delete(sender, **kwargs):
    """
    database pre delete signal. Removes database from the engine
    """
    database = kwargs.get("instance")
    LOG.debug("database pre-delete triggered")
    engine = factory_for(database.instance)
    engine.remove_database(database)

@receiver(post_save, sender=Database)
def database_post_save(sender, **kwargs):
    """
    database post save signal. Creates the database in the driver and creates a new credential.
    """
    database = kwargs.get("instance")
    is_new = kwargs.get("created")
    LOG.debug("database post-save triggered")
    if is_new:
        LOG.info("a new database (%s) were created... provision it in the engine" % (database.name))
        engine = factory_for(database.instance)
        engine.create_database(database)


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
