# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


def get_engine_type(*args):
    engine_type, created = models.EngineType.objects.get_or_create(name='mongodb')
    return engine_type


def get_engine(*args):
    engine, created = models.Engine.objects.get_or_create(engine_type=get_engine_type(), version='2.4.5')
    return engine


class EngineTypeFactory(factory.Factory):
    FACTORY_FOR = models.EngineType

    name = factory.Sequence(lambda n: 'blabla-{0}'.format(n))


class EngineFactory(factory.Factory):
    FACTORY_FOR = models.Engine

    version = '2.4.5'
    engine_type = factory.LazyAttribute(get_engine_type)


class PlanFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Plan

    name = factory.Sequence(lambda n: 'plan-{0}'.format(n))
    is_active = True
    is_default = True
    engine_type = factory.LazyAttribute(get_engine_type)


class DatabaseInfraFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseInfra

    name = factory.Sequence(lambda n: 'databaseinfra-{0}'.format(n))
    user = 'admin'
    password = '123456'
    engine = factory.LazyAttribute(get_engine)
    plan = factory.SubFactory(PlanFactory)


class NodeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Node

    address = '127.0.0.1'
    port = 27017
    is_active = True
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)


