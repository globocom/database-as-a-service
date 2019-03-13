# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from . import factory
from ..models import Organization
from drivers import base

import logging

LOG = logging.getLogger(__name__)


class AccountTest(TestCase):

    def setUp(self):
        self.organization = factory.OrganizationFactory()

    def test_create_organization(self):
        """
        Tests organization creation
        """
        self.assertTrue(self.organization.pk)
