# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError
from django.db import transaction

from ..models import Engine, EngineType


class EngineTestCase(TestCase):

    """
    Tests Engine and EngineType
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.new_engine_type = EngineType.objects.create(name="Test")

    def tearDown(self):
        self.new_engine_type.delete()

    def test_create_engine_type(self):

        engine_type = EngineType.objects.create(name="John...1..2..3..")

        self.assertTrue(engine_type.id)

    def test_error_duplicate_engine_type(self):
        with transaction.atomic():
            self.assertRaises(
                IntegrityError, EngineType.objects.create, name="Test")

    def test_create_engine_in_bd(self):

        engine_type = EngineType.objects.create(name="Maria")

        self.assertTrue(engine_type.id)

        engine = Engine.objects.create(
            version="1.2.3", engine_type=engine_type)

        self.assertTrue(engine.id)
