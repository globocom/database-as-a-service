# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError

from .factory import HostFactory


class HostTestCase(TestCase):

    def setUp(self):
        self.host = HostFactory(hostname='unique_localhost')


    def test_create_host(self):

        host = HostFactory()
        self.assertTrue(host.id)

    def test_unique_host(self):

        another_instance = self.host
        another_instance.id = None
        
        self.assertRaises(IntegrityError, another_instance.save)

        