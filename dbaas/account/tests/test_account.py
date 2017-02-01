# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError
from . import factory
from ..models import AccountUser
from drivers import base

import logging

LOG = logging.getLogger(__name__)


class AccountTest(TestCase):

    def setUp(self):
        self.new_user = factory.AccountUserFactory()

    def test_create_new_user(self):
        """
        Tests new_user creation
        """
        self.assertTrue(self.new_user.pk)

    def test_new_user_is_staff(self):
        """
        Tests new_user is staff
        """
        self.assertTrue(self.new_user.is_staff)

    def test_create_new_user_is_active(self):
        """
        Tests new_user is active
        """
        self.assertTrue(self.new_user.is_active)
