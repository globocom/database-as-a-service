# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models
from physical.tests.factory import DatabaseInfraFactory


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Project

    name = factory.Sequence(lambda n: 'project_{0}'.format(n))
    is_active = True
    slug = factory.LazyAttribute(lambda p: p.name)


class DatabaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Database

    name = factory.Sequence(lambda n: 'db_{0}'.format(n))
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    project = factory.SubFactory(ProjectFactory)


class CredentialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Credential

    user = factory.Sequence(lambda n: 'usr_{0}'.format(n))
    password = '123456'
    database = factory.SubFactory(DatabaseFactory)




