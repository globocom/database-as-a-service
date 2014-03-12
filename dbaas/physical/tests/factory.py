# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


class EnvironmentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Environment

    name = factory.Sequence(lambda n: 'env-{0}'.format(n))


class EngineTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.EngineType
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = "fake"


class EngineFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Engine
    FACTORY_DJANGO_GET_OR_CREATE = ('version', 'engine_type',)

    version = 'unique'
    engine_type = factory.SubFactory(EngineTypeFactory)


class HostFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Host

    hostname = factory.Sequence(lambda n: 'host{0}.mydomain.com'.format(n))


class PlanFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Plan

    name = factory.Sequence(lambda n: 'plan-{0}'.format(n))
    is_active = True
    is_default = True
    engine_type = factory.SubFactory(EngineTypeFactory)

    @factory.post_generation
    def environments(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for env in extracted:
                self.environments.add(env)
        else:
            self.environments.add(EnvironmentFactory())


class DatabaseInfraFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseInfra

    name = factory.Sequence(lambda n: 'databaseinfra-{0}'.format(n))
    user = 'admin'
    password = '123456'
    endpoint = '127.0.0.1:1111'
    engine = factory.SubFactory(EngineFactory)
    capacity = 2

    @factory.lazy_attribute
    def environment(self):
        # because environment is part of plan many-to-many relation, I use
        # lazy attribute instead subfactory, to ensure environment is persisted
        # since I used BUILD STRATEGY
        return EnvironmentFactory()

    @factory.lazy_attribute
    def plan(self):
        return PlanFactory(environments=[self.environment])


class InstanceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Instance

    address = '127.0.0.1'
    port = 27017
    is_active = True
    is_arbiter = False
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    hostname = factory.SubFactory(HostFactory)
