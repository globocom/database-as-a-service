from mock import patch, MagicMock, PropertyMock

from django.core.exceptions import ObjectDoesNotExist

from physical.tests import factory as physical_factory
from workflow.tests.test_host_provider import BaseCreateVirtualMachineTestCase


__all__ = ('DestroyVirtualMachineTestCase', )


@patch('physical.models.Instance.is_database', new_callable=PropertyMock)
@patch('workflow.steps.util.base.BaseInstanceStep.create', new_callable=PropertyMock)
class DestroyVirtualMachineTestCase(BaseCreateVirtualMachineTestCase):

    def setUp(self):
        super(DestroyVirtualMachineTestCase, self).setUp()
        self.host = physical_factory.HostFactory.create()
        self.instance.hostname = self.host
        self.instance.save()
        self.host_provider.provider.destroy_host = MagicMock()
        self.host_provider.delete_instance = MagicMock()
        self.host.delete = MagicMock()

    def test_destroy_host(self, create_mock, is_database_mock):
        self.host_provider.undo()

        self.assertTrue(self.host_provider.provider.destroy_host.called)
        self.assertTrue(self.host_provider.delete_instance.called)
        self.assertTrue(self.host.delete.called)

    @patch(
        'physical.models.Instance.hostname',
        new_callable=PropertyMock,
        side_effect=ObjectDoesNotExist
    )
    def test_destroy_only_instance(self, hostname_mock, create_mock, is_database_mock):

        self.host_provider.undo()

        self.assertFalse(self.host_provider.provider.destroy_host.called)
        self.assertTrue(self.host_provider.delete_instance.called)
        self.assertFalse(self.host.delete.called)
