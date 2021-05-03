from mock import MagicMock, patch, PropertyMock
from collections import namedtuple

from workflow.steps.util.foreman import DeleteHost, FqdnNotFoundExepition
from workflow.steps.tests.base import StepBaseTestCase


FAKE_VM_PROPERTIES = namedtuple('FakeVmProperties', 'id fqdn')(
    'fake_id', 'fake_fqdn.globoi.com'
)


class ReverseIpTestCase(StepBaseTestCase):
    step_class = DeleteHost

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.foreman.subprocess.check_output',
           return_value=('fake_reverse_ip.globoi.com.'))
    def test_call_subprocess_if_vm_is_up(self, check_output_mock):
        self.step.reverse_ip
        self.assertTrue(check_output_mock.called)

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.foreman.subprocess.check_output',
           return_value=('fake_reverse_ip.globoi.com.'))
    def test_remove_dot_from_reverse_ip_when_vm_up(self, check_output_mock):
        reverse_ip = self.step.reverse_ip
        self.assertEqual(reverse_ip, 'fake_reverse_ip.globoi.com')

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('workflow.steps.util.foreman.subprocess.check_output',
           return_value=('fake_reverse_ip.globoi.com'))
    def test_do_nothing_when_reverse_ip_dont_have_dot(self, check_output_mock):
        reverse_ip = self.step.reverse_ip
        self.assertEqual(reverse_ip, 'fake_reverse_ip.globoi.com')

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('workflow.steps.util.foreman.subprocess.check_output')
    @patch.object(DeleteHost, 'fqdn', new_callable=PropertyMock)
    def test_call_fqdn_property_when_vm_is_down(self, fqdn_mock,
                                                check_output_mock):
        self.step.reverse_ip
        self.assertTrue(fqdn_mock.called)
        self.assertFalse(check_output_mock.called)


class DeleteHostFQDNTestCase(StepBaseTestCase):
    step_class = DeleteHost

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=FAKE_VM_PROPERTIES))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=True))
    @patch('physical.models.HostSSH.run_script',
           return_value={'stdout': ['fake_fqdn.globo.com']})
    def test_get_fqdn_from_vm(self, run_script_mock):
        fqdn = self.step.fqdn
        self.assertTrue(run_script_mock.called)
        self.assertEqual(fqdn, 'fake_fqdn.globo.com')

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=FAKE_VM_PROPERTIES))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('physical.models.HostSSH.run_script')
    def test_get_fqdn_from_host_provider_api(self, run_script_mock):
        fqdn = self.step.fqdn
        self.assertFalse(run_script_mock.called)
        self.assertEqual('fake_fqdn.globoi.com', fqdn)

    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host',
           new=MagicMock(return_value=None))
    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('physical.models.HostSSH.run_script')
    def test_vm_properties_none(self, run_script_mock):
        with self.assertRaises(FqdnNotFoundExepition):
            self.step.fqdn

    @patch('workflow.steps.util.foreman.HostStatus.is_up',
           new=MagicMock(return_value=False))
    @patch('physical.models.HostSSH.run_script')
    @patch('workflow.steps.util.foreman.HostProviderClient.get_vm_by_host')
    def test_get_fqdn_empty_from_host_provider_api(self, get_vm_by_host_mock,
                                                   run_script_mock):
        fake_vm_properties = namedtuple('FakeVmProperties', 'id fqdn')(
            'fake_id', ''
        )
        get_vm_by_host_mock.return_value = fake_vm_properties
        with self.assertRaises(FqdnNotFoundExepition):
            self.step.fqdn
