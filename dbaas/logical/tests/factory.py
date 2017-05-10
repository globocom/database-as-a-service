# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models
from physical.tests.factory import DatabaseInfraFactory
from account.tests.factory import TeamFactory


class ProjectFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Project

    name = factory.Sequence(lambda n: 'project_{0}'.format(n))
    description = factory.Sequence(lambda n: 'project_{0}'.format(n))
    is_active = True
    slug = factory.LazyAttribute(lambda p: p.name)


class DatabaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Database

    name = factory.Sequence(lambda n: 'db_{0}'.format(n))
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    project = factory.SubFactory(ProjectFactory)
    team = factory.SubFactory(TeamFactory)
    description = factory.Sequence(lambda n: 'desc{0}'.format(n))
    used_size_in_bytes = 200 * 1024

    @factory.lazy_attribute
    def environment(self):
        # because environment is part of plan many-to-many relation, I use
        # lazy attribute instead subfactory, to ensure environment is persisted
        return self.databaseinfra.environment


class CredentialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Credential

    user = factory.Sequence(lambda n: 'usr_{0}'.format(n))
    password = '123456'
    database = factory.SubFactory(DatabaseFactory)
