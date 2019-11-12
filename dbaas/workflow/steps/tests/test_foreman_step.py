from mock import MagicMock, patch
from collections import namedtuple

from workflow.steps.util.foreman import DeleteHost, FqdnNotFoundExepition
from workflow.steps.tests.base import StepBaseTestCase


FAKE_VM_PROPERTIES = namedtuple('FakeVmProperties', 'id fqdn')(
    'fake_id', 'fake_fqdn.globoi.com'
)


class DeleteHostFQDNTestCase(StepBaseTestCase):
    step_class = DeleteHost

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=FAKE_VM_PROPERTIES))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.foreman.exec_command_on_host',
           return_value=({'stdout': ['fake_fqdn.globo.com']}, 0,))
    def test_get_fqdn_from_vm(self, exec_remote_cmd_mock):
        fqdn = self.step.fqdn
        self.assertTrue(exec_remote_cmd_mock.called)
        self.assertEqual(fqdn, 'fake_fqdn.globo.com')

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=FAKE_VM_PROPERTIES))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.foreman.exec_command_on_host')
    def test_get_fqdn_from_host_provider_api(self, exec_remote_cmd_mock):
        fqdn = self.step.fqdn
        self.assertFalse(exec_remote_cmd_mock.called)
        self.assertEqual('fake_fqdn.globoi.com', fqdn)

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=None))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.foreman.exec_command_on_host')
    def test_vm_properties_none(self, exec_remote_cmd_mock):
        with self.assertRaises(FqdnNotFoundExepition):
            self.step.fqdn

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.foreman.exec_command_on_host')
    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host')
    def test_get_fqdn_empty_from_host_provider_api(self, get_vm_by_host_mock,
                                                   exec_remote_cmd_mock):
        fake_vm_properties = namedtuple('FakeVmProperties', 'id fqdn')(
            'fake_id', ''
        )
        get_vm_by_host_mock.return_value = fake_vm_properties
        with self.assertRaises(FqdnNotFoundExepition):
            self.step.fqdn
