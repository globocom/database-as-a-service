# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase

from ..models import Plan
from .factory import PlanFactory


class PlanTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_there_can_be_only_one_default_plan(self):
        """
        Highlander test
        """

        plan = PlanFactory()

        self.assertTrue(plan.is_default)

        plan_2 = PlanFactory()

        self.assertTrue(plan_2.is_default)

        plan = Plan.objects.get(id=plan.id)
        self.assertFalse(plan.is_default)

        default_plans = Plan.objects.filter(
            is_default=True, engine=plan_2.engine)
        self.assertEqual(default_plans.count(), 1)
