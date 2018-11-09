from mock import patch, MagicMock, PropertyMock

from physical.tests import factory as physical_factory
from workflow.tests.test_host_provider import BaseCreateVirtualMachineTestCase


__all__ = ('CreateVirtualMachineTestCase',)


@patch('physical.models.Instance.is_database', new_callable=PropertyMock)
@patch('workflow.steps.util.base.BaseInstanceStep.create', new_callable=PropertyMock)
class CreateVirtualMachineTestCase(BaseCreateVirtualMachineTestCase):

    def setUp(self):
        super(CreateVirtualMachineTestCase, self).setUp()
        self.host_provider.provider.create_host = MagicMock()
        self.host_provider.create_instance = MagicMock()

    def test_set_weaker_offering_when_no_database_instance(self, create_mock, is_database_mock):
        is_database_mock.return_value = False

        self.host_provider.do()

        create_host_func = self.host_provider.provider.create_host

        self.assertTrue(create_host_func.called)
        self.assertTrue(self.host_provider.create_instance.called)
        self.assertEqual(self.infra.last_vm_created, 1)

        create_host_call_args = create_host_func.call_args[0]
        call_offering = create_host_call_args[1]
        self.assertEqual(call_offering, self.weaker_offering)

    def test_set_stronger_offering_when_no_database_instance(self, create_mock, is_database_mock):
        is_database_mock.return_value = True

        self.host_provider.do()

        create_host_func = self.host_provider.provider.create_host

        self.assertTrue(create_host_func.called)
        self.assertTrue(self.host_provider.create_instance.called)
        self.assertEqual(self.infra.last_vm_created, 1)

        create_host_call_args = create_host_func.call_args[0]
        call_offering = create_host_call_args[1]
        self.assertEqual(call_offering, self.stronger_offering)

    def test_not_create_host_when_have_one_instance_with_same_dns(self, create_mock, is_database_mock):
        instance2 = physical_factory.InstanceFactory.create(
            dns=self.instance.dns
        )
        self.host_provider.instance = instance2
        is_database_mock.return_value = False

        self.host_provider.do()

        self.assertFalse(self.host_provider.provider.create_host.called)
        self.assertTrue(self.host_provider.create_instance.called)
        self.assertEqual(self.infra.last_vm_created, 0)

        create_instance_call_args = self.host_provider.create_instance.call_args[0]
        call_host = create_instance_call_args[0]
        self.assertEqual(instance2.hostname.id, call_host.id)
