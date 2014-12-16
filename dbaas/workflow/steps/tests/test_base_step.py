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

    def test_do_requires_workflow_dict(self):
        try:
            self.base_step.do()
        except TypeError:
            exception = True

        self.assertTrue(exception)

    def test_undo_requires_workflow_dict(self):
        try:
            self.base_step.undo()
        except TypeError:
            exception = True

        self.assertTrue(exception)
