from mock import patch, MagicMock, PropertyMock

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist

from physical.models import Instance
from physical.tests import factory as physical_factory
from workflow.steps.util.host_provider import CreateVirtualMachine


class BaseCreateVirtualMachineTestCase(TestCase):
    def _create_instance(self):
        inst = Instance()
        inst.address = '127.0.0.1'
        inst.port = 27017
        inst.is_active = True
        inst.databaseinfra = physical_factory.DatabaseInfraFactory.create(
            plan=self.plan
        )
        inst.status = 1
        inst.instance_type = 2
        inst.total_size_in_bytes = 100
        inst.used_size_in_bytes = 50
        #TODO: Fix that vm_name. See better way to set vm_name not on instance directly
        inst.vm_name = inst.dns

        return inst

    def setUp(self):
        self.weaker_offering = physical_factory.OfferingFactory.create(
            name='weaker_offering',
            memory_size_mb=1,
            cpus=1
        )
        self.stronger_offering = physical_factory.OfferingFactory.create(
            name='stronger_offering',
            memory_size_mb=9,
            cpus=9
        )
        self.plan = physical_factory.PlanFactory(
            weaker_offering=self.weaker_offering,
            stronger_offering=self.stronger_offering
        )
        self.instance = self._create_instance()
        self.infra = self.instance.databaseinfra

        self.host_provider = CreateVirtualMachine(self.instance)


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
