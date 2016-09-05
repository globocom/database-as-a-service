# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from ..forms.database_infra import DatabaseInfraForm
from . import factory


class FormDatabaseInfraTestCase(TestCase):

    def setUp(self):
        self.engine = factory.EngineFactory()
        self.plan = factory.PlanFactory(engine_type=self.engine.engine_type)
        self.disk_offering = factory.DiskOfferingFactory()

    def _build_basic_form_data(self, plan, disk_offering):
        return ({
            'plan': plan,
            'disk_offering': disk_offering
        })

    def test_can_create_form_without_args(self):
        form = DatabaseInfraForm()
        self.assertIsNotNone(form)

    def test_can_create_form(self):
        data = self._build_basic_form_data(self.plan.id, self.disk_offering.id)
        form = DatabaseInfraForm(data)

        self.assertEqual(form.data['plan'], self.plan.id)
        self.assertEqual(form.data['disk_offering'], self.disk_offering.id)


    def test_can_create_form_without_plan(self):
        data = self._build_basic_form_data(None, self.disk_offering.id)
        form = DatabaseInfraForm(data)

        self.assertIsNone(form.data['plan'])
        self.assertEqual(form.data['disk_offering'], self.disk_offering.id)

    def test_can_create_form_without_plan_and_disk(self):
        data = self._build_basic_form_data(None, None)
        form = DatabaseInfraForm(data)

        self.assertIsNone(form.data['plan'])
        self.assertIsNone(form.data['disk_offering'])

    def test_can_create_form_without_disk_and_no_plan_disk(self):
        plan_without_disk = factory.PlanFactory(
            engine_type=self.engine.engine_type
        )
        plan_without_disk.disk_offering = None
        plan_without_disk.save()

        data = self._build_basic_form_data(plan_without_disk.id, None)
        form = DatabaseInfraForm(data)

        self.assertEqual(form.data['plan'], plan_without_disk.id)
        self.assertIsNone(form.data['disk_offering'])

    def test_can_create_form_without_disk(self):
        data = self._build_basic_form_data(self.plan.id, None)
        form = DatabaseInfraForm(data)

        self.assertEqual(form.data['plan'], self.plan.id)
        self.assertEqual(
            form.data['disk_offering'], self.plan.disk_offering.id
        )
