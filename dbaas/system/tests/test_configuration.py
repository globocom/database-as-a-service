# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
# from . import factory
from ..models import Configuration


import logging

LOG = logging.getLogger(__name__)


class ConfigurationTest(TestCase):

    # def setUp(self):
    #     self.new_user = factory.UserFactory()

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
            Configuration.get_by_name_all_fields("newcfg").name, conf_name)
