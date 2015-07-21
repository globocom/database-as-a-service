# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from ..models import Instance
from .factory import DatabaseInfraFactory, HostFactory, InstanceFactory


class InstanceTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.databaseinfra = DatabaseInfraFactory()
        self.hostname = HostFactory()
        self.new_instance = InstanceFactory(address="new_instance.localinstance",
                                            port=123,
                                            is_active=True,
                                            is_arbiter=False,
                                            databaseinfra=self.databaseinfra)

    def test_create_instance(self):

        instance = Instance.objects.create(address="test.localinstance",
                                           port=123,
                                           is_active=True,
                                           is_arbiter=False,
                                           hostname=self.hostname,
                                           databaseinfra=self.databaseinfra)

        self.assertTrue(instance.id)

    def test_error_duplicate_instance(self):

        another_instance = self.new_instance
        another_instance.id = None

        self.assertRaises(IntegrityError, another_instance.save)

    def test_cleanup_without_engine_raises_exception(self):
        self.new_instance.databaseinfra.engine_id = None
        self.assertRaises(ValidationError, self.new_instance.clean)
