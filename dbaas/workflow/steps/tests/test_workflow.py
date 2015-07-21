# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from workflow.workflow import start_workflow
from workflow.workflow import stop_workflow

LOG = logging.getLogger(__name__)


class StartWorkflowTestCase(TestCase):

    def setUp(self):
        self.workflow_dict = {}
        self.workflow_dict['steps'] = ('workflow.steps.tests.factory.TestStep1',
                                       'workflow.steps.tests.factory.TestStep2')
        self.start_worflow = start_workflow(self.workflow_dict)

    def test_start_workflow_without_steps(self):
        self.assertFalse(start_workflow({}))

    def test_start_workflow_returns_true(self):
        self.assertTrue(self.start_worflow)

    def test_workflow_dict_vars(self):
        self.assertEqual(self.workflow_dict['total_steps'], 2)
        self.assertEqual(self.workflow_dict['created'], True)
        self.assertEqual(self.workflow_dict['status'], 1)
        self.assertEqual(
            self.workflow_dict['exceptions'], {'error_codes': [], 'traceback': []})
        self.assertEqual(self.workflow_dict['exceptions']['traceback'], [])
        self.assertEqual(self.workflow_dict['exceptions']['error_codes'], [])

    def workflow_error_throws_rollback(self):
        self.workflow_dict['steps'] = ('workflow.steps.tests.factory.TestStep2',
                                       'workflow.steps.tests.factory.TestStep3')

        self.start_worflow = start_workflow(self.workflow_dict)
        self.assertEqual(self.workflow_dict['total_steps'], 2)
        self.assertEqual(self.workflow_dict['created'], False)
        self.assertEqual(self.workflow_dict['status'], 0)
        self.assertEqual(self.workflow_dict['exceptions']['error_codes'], [
                         ('DBAAS_0001', 'Workflow error')])
        self.assertEqual(
            self.workflow_dict['steps'], (u'workflow.steps.tests.factory.TestStep3',))


class StopWorkflowTestCase(TestCase):

    def setUp(self):
        self.workflow_dict = {}
        self.workflow_dict['steps'] = ('workflow.steps.tests.factory.TestStep1',
                                       'workflow.steps.tests.factory.TestStep2')
        self.stop_workflow = stop_workflow(self.workflow_dict)

    def test_stop_workflow_without_steps(self):
        self.assertFalse(stop_workflow({}))

    def test_stop_workflow_returns_true(self):
        self.assertTrue(self.stop_workflow)

    def test_workflow_dict_vars(self):
        self.assertEqual(self.workflow_dict['total_steps'], 2)
        self.assertEqual(
            self.workflow_dict['exceptions'], {'error_codes': [], 'traceback': []})
        self.assertEqual(self.workflow_dict['exceptions']['traceback'], [])
        self.assertEqual(self.workflow_dict['exceptions']['error_codes'], [])

    def workflow_error_throws_exception(self):
        self.workflow_dict['steps'] = ('workflow.steps.tests.factory.TestStep4',
                                       'workflow.steps.tests.factory.TestStep3')

        self.start_worflow = stop_workflow(self.workflow_dict)
        self.assertEqual(self.workflow_dict['total_steps'], 2)
        self.assertEqual(self.workflow_dict['exceptions']['error_codes'], [
                         ('DBAAS_0001', 'Workflow error')])
        self.assertEqual(self.workflow_dict['steps'], ('workflow.steps.tests.factory.TestStep4',
                                                       'workflow.steps.tests.factory.TestStep3'))
