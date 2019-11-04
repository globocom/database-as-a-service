from unittest import TestCase
from mock import PropertyMock, MagicMock, patch

from workflow.steps.util.database import StopIfRunning, StopSlaveIfRunning
from physical.tests.factory import InstanceFactory


class StopIfRunningTestCase(TestCase):
    def setUp(self):
        self.instance = InstanceFactory.build()
        self.step = StopIfRunning(self.instance)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=None))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_not_valid_when_dosent_have_host(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=False))
    def test_have_host_but_is_down(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_is_valid(self):
        self.assertTrue(self.step.is_valid)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_unicode_valid(self):
        self.assertEqual(
            str(self.step),
            'Stopping database...'
        )

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=False))
    def test_unicode_not_valid(self):
        self.assertEqual(
            str(self.step),
            'Stopping database...SKIPPED! because database is stopped...'
        )


class StopSlaveIfRunningTestCase(TestCase):
    def setUp(self):
        self.instance = InstanceFactory.build()
        self.step = StopSlaveIfRunning(self.instance)

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=False))
    def test_db_is_down(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_db_is_up(self):
        self.assertTrue(self.step.is_valid)

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_unicode_is_valid(self):
        self.assertEqual(
            str(self.step),
            'Stopping slave...'
        )

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=False))
    def test_unicode_not_valid(self):
        self.assertEqual(
            str(self.step),
            'Stopping slave...SKIPPED! because database is stopped...'
        )
