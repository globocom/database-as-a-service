from mock import MagicMock, patch

from workflow.steps.util.host_provider import StopIfRunning
from workflow.steps.tests.base import StepBaseTestCase


class StopIfRunningTestCase(StepBaseTestCase):
    step_class = StopIfRunning

    @patch('workflow.steps.util.host_provider.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.host_provider.Provider.stop')
    def test_stop_not_called(self, stop_mock):
        self.step.do()
        self.assertFalse(stop_mock.called)

    @patch('workflow.steps.util.host_provider.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.host_provider.Provider.stop')
    def test_stop_called(self, stop_mock):
        self.step.do()
        self.assertTrue(stop_mock.called)
