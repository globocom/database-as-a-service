# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
import datetime
from django.db import models
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField
from django.utils.functional import cached_property
from util import slugify, make_db_random_password
from util.models import BaseModel
from physical.models import DatabaseInfra
from drivers import factory_for

LOG = logging.getLogger(__name__)


class Project(BaseModel):

    name = models.CharField(verbose_name=_("Project name"), max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name=_("Is project active"), default=True)
    slug = models.SlugField()

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        permissions = (
            ("view_project", "Can view projects"),
        )


class Database(BaseModel):

    RESERVED_DATABASES_NAME = ('admin', 'config', 'local')

    name = models.CharField(verbose_name=_("Database name"), max_length=100)
    databaseinfra = models.ForeignKey(DatabaseInfra, related_name="databases", on_delete=models.PROTECT)
    project = models.ForeignKey(Project, related_name="databases", on_delete=models.PROTECT, null=True, blank=True)
    group = models.ForeignKey(Group, related_name="databases",
                                 help_text=_("Group that is accountable for the database"),
                                 null=True,
                                 blank=True)
    is_in_quarantine = models.BooleanField(verbose_name=_("Is database in quarantine?"), default=False)
    quarantine_dt = models.DateField(verbose_name=_("Quarantine date"), null=True, blank=True, editable=False)

    def __unicode__(self):
        return u"%s" % self.name

    class Meta:
        permissions = (
            ("can_manage_quarantine_databases", "Can manage databases in quarantine"),
            ("view_database", "Can view databases"),
        )
        unique_together = (
            ('name', 'databaseinfra'),
        )
        
        ordering = ('databaseinfra', 'name',)

    def delete(self, *args, **kwargs):
        """
        Overrides the delete method so that a database can be put in quarantine and not removed
        """
        #do_something()
        if self.is_in_quarantine:
            LOG.warning("Database %s is in quarantine and will be removed" % self.name)
            super(Database, self).delete(*args, **kwargs)  # Call the "real" delete() method.
        else:
            LOG.warning("Putting database %s in quarantine" % self.name)
            if self.credentials.exists():
                for credential in self.credentials.all():
                    new_password = make_db_random_password()
                    new_credential = Credential.objects.get(pk=credential.id)
                    new_credential.password = new_password
                    new_credential.save()

                    instance = factory_for(self.databaseinfra)
                    instance.update_user(new_credential)

            else:
                LOG.info("There is no credential on this database: %s" % self.databaseinfra)

            self.is_in_quarantine = True
            self.quarantine_dt = datetime.datetime.now().date()
            self.save()

    def clean(self):

        if self.name in self.__get_database_reserved_names():
            raise ValidationError(_("%s is a reserved database name" % self.name))

    def create_new_credential(self):
        """creates a new credential for the database with a random password"""
        engine = factory_for(self.databaseinfra)
        LOG.info("creating new credential for database %s" % self.name)
        credential = Credential(user=Credential.USER_PATTERN % self.name, password=make_db_random_password(), database=self)
        credential.save()
        engine.create_user(credential)
        return credential

    @classmethod
    def provision(cls, name, plan):
        # create new databaseinfra

        LOG.debug("provisioning databaseinfra with plan: %s | name: %s", plan, name)

        database = Database()
        database.databaseinfra = DatabaseInfra.best_for(plan)
        database.name = name
        database.save()
        return database

    def __get_database_reserved_names(self):
        return Database.RESERVED_DATABASES_NAME

    @cached_property
    def driver(self):
        return self.databaseinfra.get_driver()

    def get_endpoint(self):
        return self.driver.get_connection() + '/' + self.name

    endpoint = property(get_endpoint)

    @cached_property
    def database_status(self):
        info = self.driver.info()
        database_status = info.get_database_status(self.name)
        return database_status

    @property
    def infra(self):
        """ Total size of database (in bytes) """
        return self.databaseinfra

    @property
    def total_size(self):
        """ Total size of database (in bytes) """
        return self.database_status.total_size_in_bytes

    @property
    def used_size(self):
        """ Used size of database (in bytes) """
        return self.database_status.used_size_in_bytes

    @property
    def capacity(self):
        """ Float number about used capacity """
        return 1.0 * self.used_size / self.total_size if self.total_size else 0


class Credential(BaseModel):

    USER_PATTERN = "u_%s"

    user = models.CharField(verbose_name=_("User name"), max_length=100)
    password = EncryptedCharField(verbose_name=_("User password"), max_length=255)
    database = models.ForeignKey(Database, related_name="credentials")

    def __unicode__(self):
        return u"%s" % self.user

    class Meta:
        permissions = (
            ("view_credential", "Can view credentials"),
        )
        unique_together = (
            ('user', 'database'),
        )
        ordering = ('database', 'user',)

    @cached_property
    def driver(self):
        return self.database.databaseinfra.get_driver()

    def reset_password(self):
        """ Reset credential password to a new random password """
        self.password = make_db_random_password()
        self.driver.update_user(self)
        self.save()

    @classmethod
    def create_new_credential(cls, user, database):
        credential = Credential()
        credential.database = database
        credential.user = user
        credential.password = make_db_random_password()
        credential.driver.create_user(credential)
        credential.full_clean()
        credential.save()
        return credential


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
    engine = factory_for(database.databaseinfra)
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
        engine = factory_for(database.databaseinfra)
        engine.create_database(database)
        database.create_new_credential()


@receiver(pre_save, sender=Database)
def database_pre_save(sender, **kwargs):
    database = kwargs.get('instance')
    if database.is_in_quarantine:
        if database.quarantine_dt is None:
            database.quarantine_dt = datetime.datetime.now().date()
    else:
        database.quarantine_dt = None

    #slugify name
    database.name = slugify(database.name)

    if database.id:
        saved_object = Database.objects.get(id=database.id)
        if database.name != saved_object.name:
            raise AttributeError(_("Attribute name cannot be edited"))


@receiver(pre_save, sender=Credential)
def credential_pre_save(sender, **kwargs):
    credential = kwargs.get('instance')

    #slugify user
    credential.user = slugify(credential.user)

    if credential.id:
        saved_object = Credential.objects.get(id=credential.id)
        if credential.user != saved_object.user:
            raise AttributeError(_("Attribute user cannot be edited"))

        if credential.database != saved_object.database:
            raise AttributeError(_("Attribute database cannot be edited"))


simple_audit.register(Project, Database, Credential)
