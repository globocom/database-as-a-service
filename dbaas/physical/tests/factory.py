# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


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


class DatabaseInfraFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseInfra

    name = factory.Sequence(lambda n: 'databaseinfra-{0}'.format(n))
    user = 'admin'
    password = '123456'
    engine = factory.SubFactory(EngineFactory)
    plan = factory.SubFactory(PlanFactory)


class InstanceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Instance

    address = '127.0.0.1'
    port = 27017
    is_active = True
    is_arbiter = False
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    hostname = factory.SubFactory(HostFactory)
