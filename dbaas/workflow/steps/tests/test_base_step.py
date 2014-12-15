# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from ..util.base import BaseStep

LOG = logging.getLogger(__name__)


class BaseStepTestCase(TestCase):

    def setUp(self):
        self.base_step = BaseStep()

    def test_has_do_method(self):
        self.assertTrue(hasattr(self.base_step, 'do'))

    def test_has_undo_method(self):
        self.assertTrue(hasattr(self.base_step, 'undo'))
