# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
# from . import factory
from ..models import Configuration
import logging
import hashlib
import datetime
from . import factory

LOG = logging.getLogger(__name__)


class ConfigurationTest(TestCase):

    def setUp(self):
        self.conf_model = factory.ConfigurationFactory()

    def test_get_empty_list(self):
        """
        Tests get empty list when variable name does not exists
        """
        self.assertEquals(Configuration.get_by_name_as_list("abc"), [])

    def test_get_conf_by_name_all_fields(self):
        """
        Tests get conf by name with all fields method
        """
        conf_name = "newcfg"
        Configuration(
            name=conf_name,
            value="1",
            description="test"
        ).save()
        self.assertEquals(
            Configuration.get_by_name_all_fields(conf_name).value, "1")

    def test_validate_hash(self):
        conf = self.conf_model
        to_hash = "%s%s%s%s" % (
            conf.name,
            conf.value,
            conf.description,
            datetime.date.strftime(datetime.date.today(), "%d%m%Y")
        )

        hash = hashlib.sha256(to_hash.encode("utf8")).hexdigest()
        self.assertEquals(conf.hash, hash)

    def test_get_cache_key(self):
        conf = self.conf_model
        k = "cfg:%s" % conf.name

        self.assertEquals(conf.get_cache_key(conf.name), k)

    def test_get_by_name_as_int(self):
        conf_name = "new_conf_as_int"
        Configuration(
            name=conf_name,
            value="1",
            description="test"
        ).save()

        get_conf = Configuration.get_by_name_as_int(conf_name)
        self.assertIsInstance(get_conf, int)
        self.assertEquals(get_conf, 1)

    def test_get_by_name_as_float(self):
        conf_name = "new_conf_as_float"
        Configuration(
            name=conf_name,
            value="1.4",
            description="test"
        ).save()

        get_conf = Configuration.get_by_name_as_float(conf_name)
        self.assertIsInstance(get_conf, float)
        self.assertEquals(get_conf, 1.4)

    def test_get_by_name(self):
        conf = self.conf_model

        get_conf = Configuration.get_by_name(conf.name)
        self.assertEquals(get_conf, conf.value)
