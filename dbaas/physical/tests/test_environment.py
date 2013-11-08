# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError

from .factory import EnvironmentFactory


class HostTestCase(TestCase):

    def setUp(self):
        self.host = EnvironmentFactory(hostname='production')

    def test_create_host(self):

        env = EnvironmentFactory()
        self.assertTrue(env.id)

    def test_unique_host(self):

        another_instance = self.env
        another_instance.id = None

        self.assertRaises(IntegrityError, another_instance.save)
