# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
from . import factory
from ..models import AccountUser
from drivers import base

import logging

LOG = logging.getLogger(__name__)


class SimpleTest(TestCase):

    def setUp(self):
        self.new_user = factory.UserFactory()

    def test_create_new_use(self):

        self.assertTrue(self.new_user.pk)
