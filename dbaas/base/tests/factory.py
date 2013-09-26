# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


class DriverFactory(factory.Factory):
    FACTORY_FOR = models.Engine

    version = '2.4.5'
    engine_type_id = 1 # use fixture

class NodeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Node

    address = '127.0.0.1'
    port = 27017
    environment_id = 1
    is_active = True


class InstanceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Instance

    name = factory.Sequence(lambda n: 'instance-{0}'.format(n))
    user = 'root'
    password = '123456'
    node = factory.SubFactory(NodeFactory)
    engine_id = 1
    product = None
    plan_id = 1 # use fixture


class DatabaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Database

    name = factory.Sequence(lambda n: 'db-{0}'.format(n))
    instance = factory.SubFactory(InstanceFactory)


class CredentialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Credential

    user = factory.Sequence(lambda n: 'usr_{0}'.format(n))
    password = '123456'
    database = factory.SubFactory(DatabaseFactory)


