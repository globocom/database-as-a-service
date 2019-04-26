# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib import admin
from physical.admin.cloud import CloudAdmin
from .factory import CloudFactory
from physical.models import Cloud


class CloudTestCase(TestCase):

    def setUp(self):
        self.cloud = CloudFactory()

    def test_create_cloud(self):
        """
        Tests cloud creation
        """
        self.assertTrue(self.cloud.pk)
