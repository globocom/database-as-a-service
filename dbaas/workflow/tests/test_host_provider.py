from mock import patch, MagicMock, PropertyMock
from django.test import TestCase
from physical.tests import factory as physical_factory
from workflow.steps.util.host_provider import CreateVirtualMachine
from physical.models import Instance


class CreateVirtualMachineTestCase(TestCase):

    def _create_instance(self):
        inst = Instance()
        inst.address = '127.0.0.1'
        inst.port = 27017
        inst.is_active = True
        inst.databaseinfra = physical_factory.DatabaseInfraFactory.create()
        inst.status = 1
        inst.instance_type = 2
        inst.total_size_in_bytes = 100
        inst.used_size_in_bytes = 50
        #TODO: Fix that vm_name. See better way to set vm_name not on instance directly
        inst.vm_name = inst.dns

        return inst

    def setUp(self):
        # self.instance = physical_factory.InstanceFactory.build()
        self.instance = self._create_instance()
        self.databaseinfra = self.instance.databaseinfra
        # self.engine = FakeDriver(databaseinfra=self.databaseinfra)
        self.environment = physical_factory.EnvironmentFactory()
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
        self.weaker_plan = physical_factory.PlanFactory(
            weaker_offering=self.weaker_offering,
            stronger_offering=self.stronger_offering
        )

        import ipdb; ipdb.set_trace()
        self.host_provider = CreateVirtualMachine(self.instance)

    @patch('physical.models.Instance.is_database', new_callable=PropertyMock)
    @patch('workflow.steps.util.base.BaseInstanceStep.create', new_callable=PropertyMock)
    def test_set_weaker_offering_when_no_database_instance(self, create_mock, is_database_mock):
        self.host_provider.provider.create_host = MagicMock()
        self.host_provider.create_instance = MagicMock()
        is_database_mock.return_value = False

        self.host_provider.do()

        create_host_func = self.host_provider.provider.create_host

        self.assertTrue(create_host_func.called)

        create_host_call_args = create_host_func.call_args[0]
        call_offering = create_host_call_args[1]
        self.assertEqual(call_offering, self.weaker_offering)
