from mock import PropertyMock, MagicMock, patch

from workflow.steps.util.database import (StopIfRunning, StopSlaveIfRunning,
                                          StopIfRunningAndVMUp)
from workflow.steps.tests.base import StepBaseTestCase


class StopIfRunningTestCase(StepBaseTestCase):
    step_class = StopIfRunning

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


class StopIfRunningAndVMUpTestCase(StepBaseTestCase):
    step_class = StopIfRunningAndVMUp

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.database.StopIfRunning.vm_is_up',
           new=MagicMock(return_value=False))
    def test_vm_down(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.database.StopIfRunning.vm_is_up',
           new=MagicMock(return_value=True))
    def test_vm_up_but_db_down(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopIfRunning.host',
           new=PropertyMock(return_value=MagicMock()))
    @patch('workflow.steps.util.database.StopIfRunning.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.database.StopIfRunning.vm_is_up',
           new=MagicMock(return_value=True))
    def test_is_valid(self):
        self.assertTrue(self.step.is_valid)


class StopSlaveIfRunningTestCase(StepBaseTestCase):
    step_class = StopSlaveIfRunning

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=False))
    def test_db_is_down(self):
        self.assertFalse(self.step.is_valid)

    @patch('workflow.steps.util.database.StopSlaveIfRunning.is_up',
           new=MagicMock(return_value=True))
    def test_db_is_up(self):
        self.assertTrue(self.step.is_valid)
