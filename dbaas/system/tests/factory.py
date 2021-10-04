# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from system import models


class ConfigurationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Configuration

    name = factory.Sequence(lambda n: 'conf_{0}'.format(n))
