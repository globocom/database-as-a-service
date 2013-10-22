# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models
from physical.tests.factory import InstanceFactory, NodeFactory


class ProductFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Product

    name = factory.Sequence(lambda n: 'product_{0}'.format(n))
    is_active = True
    slug = factory.LazyAttribute(lambda p: p.name)


class DatabaseFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Database

    name = factory.Sequence(lambda n: 'db-{0}'.format(n))
    instance = factory.SubFactory(InstanceFactory)
    product = factory.SubFactory(ProductFactory)


class CredentialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Credential

    user = factory.Sequence(lambda n: 'usr_{0}'.format(n))
    password = '123456'
    database = factory.SubFactory(DatabaseFactory)




