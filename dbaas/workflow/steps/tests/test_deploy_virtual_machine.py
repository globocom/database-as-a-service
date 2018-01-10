from mock import patch, MagicMock

from physical.models import Host
from physical.tests.factory import (PlanAttrFactory, DatabaseInfraOfferingFactory,
                                    CloudStackBundleFactory, CloudStackOfferingFactory)
from workflow.steps.tests import TestBaseStep
from workflow.steps.mysql.deploy.create_virtualmachines import CreateVirtualMachine as CreateVirtualMachineMySQL
from workflow.steps.mysql.deploy.create_virtualmachines_fox import CreateVirtualMachine as CreateVirtualMachineMySQLFox
from workflow.steps.redis.deploy.create_virtualmachines import CreateVirtualMachine as CreateVirtualMachineRedis
from workflow.steps.mongodb.deploy.create_virtualmachines import CreateVirtualMachine as CreateVirtualMachineMongodb
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import DatabaseInfraOffering, HostAttr


def fake_get_credentials_for(*args, **kw):
    credential_type = kw.get('credential_type')

    if credential_type == CredentialType.CLOUDSTACK:
        return type('FakeCSCredential', (), {
            'project': 'fake_project',
            'get_parameter_by_name': MagicMock(return_value=999)
        })
    elif credential_type == CredentialType.VM:
        return type('FakeVMCredential', (), {
            'user': 'fake_user',
            'password': 'fake_pass'
        })


@patch('workflow.steps.mysql.deploy.create_virtualmachines.get_credentials_for',
        new=MagicMock(side_effect=fake_get_credentials_for))
class CreateVirtualMachineMySQLSingleTestCase(TestBaseStep):

    vm_quantity = 1
    create_class = CreateVirtualMachineMySQL
    vm_count = 0
    cloudstack_provider_path = 'workflow.steps.mysql.deploy.create_virtualmachines.CloudStackProvider'
    expected_instances_quantity = None

    def _fake_deploy_virtual_machine(*args, **kw):
        fake_vm_dict = {
            'virtualmachine': [
                {
                    'id': 999,
                    'nic': [{'ipaddress': 'fake_address{}'.format(kw.get('vmname'))}]
                }
            ]
        }
        return ({}, fake_vm_dict,)

    def _create_vm_workflow(self, workflow_dict=None, expected_result=True):
        with patch(self.cloudstack_provider_path) as provider_mock:
            provider_mock().deploy_virtual_machine.side_effect = self._fake_deploy_virtual_machine
            result = self.create_vm_workflow.do(workflow_dict or self.fake_workflow_dict)
            self.assertEqual(result, expected_result)

    def _validate_instance_offering(self, instances):

        for instance in instances:
            host_instances = instance.hostname.instances.all()
            instances_count = host_instances.count()

            if (instances_count > 1 or
                 (instances_count == 1 and host_instances[0].is_database)):
                expected_offering = self.strong_offering
            else:
                expected_offering = self.weaker_offering

            self.assertEqual(instance.hostname.offering, expected_offering)

    @property
    def weaker_offering(self):
        return self.plan_attr.get_weaker_offering()

    @property
    def strong_offering(self):
        return self.plan_attr.get_stronger_offering()

    def setUp(self):
        super(CreateVirtualMachineMySQLSingleTestCase, self).setUp()
        self.infra.last_vm_created = 0
        self.infra.save()
        self.plan_attr = PlanAttrFactory.create(plan=self.plan)
        self.create_vm_workflow = self.create_class()
        self.fake_vm_names = map(lambda n: 'vm{}'.format(n), range(self.vm_quantity))
        self.fake_workflow_dict = {
            'qt': self.vm_quantity,
            'plan': self.plan,
            'environment': self.environment,
            'exceptions': {
                'error_codes': [],
                'traceback': []
            },
            'names': {
                'vms': self.fake_vm_names
            },
            'databaseinfra': self.infra

        }
        self.vm_count += 1

    def test_no_environment(self):

        self._create_vm_workflow({'plan': 'fake'}, expected_result=False)

    def test_no_plan(self):

        self._create_vm_workflow({'environment': 'fake'}, expected_result=False)

    def test_create_dbinfra_offering(self):
        self.assertEqual(DatabaseInfraOffering.objects.filter(databaseinfra=self.infra).count(), 0)
        self._create_vm_workflow()
        self.assertEqual(DatabaseInfraOffering.objects.filter(databaseinfra=self.infra).count(), 1)

    def test_exists_dbinfra_offering(self):
        DatabaseInfraOfferingFactory.create(databaseinfra=self.infra)
        self.assertEqual(DatabaseInfraOffering.objects.filter(databaseinfra=self.infra).count(), 1)
        self._create_vm_workflow()
        self.assertEqual(DatabaseInfraOffering.objects.filter(databaseinfra=self.infra).count(), 1)

    def test_create_instance(self):
        self.assertEqual(self.infra.instances.filter(address__contains='fake_address').count(), 0)
        self._create_vm_workflow()
        instances = self.infra.instances.filter(address__contains='fake_address')
        self.assertEqual(
            instances.count(),
            self.expected_instances_quantity or self.vm_quantity
        )
        self._validate_instance_offering(instances)

    def test_create_hostattr(self):
        self._create_vm_workflow()
        instance = self.infra.instances.last()
        host_attr = HostAttr.objects.get(host=instance.hostname)

        self.assertEqual(host_attr.vm_id, '999')
        self.assertEqual(host_attr.vm_user, 'fake_user')
        self.assertEqual(host_attr.vm_password, 'fake_pass')

    def test_create_host(self):
        self.assertEqual(Host.objects.filter(address__contains='fake_address').count(), 0)

        self._create_vm_workflow()

        host = Host.objects.filter(address__contains='fake_address')
        self.assertEqual(host.count(), self.vm_quantity)


class CreateVirtualMachineMySQLHATestCase(CreateVirtualMachineMySQLSingleTestCase):
    vm_quantity = 2


@patch('workflow.steps.mysql.deploy.create_virtualmachines_fox.get_credentials_for',
       new=MagicMock(side_effect=fake_get_credentials_for))
class CreateVirtualMachineMySQLFoxHATestCase(CreateVirtualMachineMySQLSingleTestCase):
    vm_quantity = 2
    create_class = CreateVirtualMachineMySQLFox
    cloudstack_provider_path = 'workflow.steps.mysql.deploy.create_virtualmachines_fox.CloudStackProvider'

    @patch('workflow.steps.mysql.deploy.create_virtualmachines_fox.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.mysql.deploy.create_virtualmachines_fox.LastUsedBundle.get_next_bundle')
    def test_not_call_last_used_bundle_when_bundles_is_1(self, next_mock, next_infra_mock):
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, 0)
        self.assertEqual(next_infra_mock.call_count, 0)

    @patch('workflow.steps.mysql.deploy.create_virtualmachines_fox.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.mysql.deploy.create_virtualmachines_fox.LastUsedBundle.get_next_bundle')
    def test_call_last_used_bundle_when_bundles_more_than_one(self, next_mock, next_infra_mock):
        self.plan_attr.bundle_group.bundles.add(CloudStackBundleFactory.create())
        next_mock.return_value = self.plan_attr.bundle_group.bundles.first()
        next_infra_mock.return_value = self.plan_attr.bundle_group.bundles.last()
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, 1)
        self.assertEqual(next_infra_mock.call_count, 1)


@patch('workflow.steps.redis.deploy.create_virtualmachines.get_credentials_for',
       new=MagicMock(side_effect=fake_get_credentials_for))
class CreateVirtualMachineRedisSingleTestCase(CreateVirtualMachineMySQLSingleTestCase):
    vm_quantity = 1
    create_class = CreateVirtualMachineRedis
    cloudstack_provider_path = 'workflow.steps.redis.deploy.create_virtualmachines.CloudStackProvider'
    expected_next_infra_count = 1
    expected_next_count = 0

    @patch('workflow.steps.redis.deploy.create_virtualmachines.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.redis.deploy.create_virtualmachines.LastUsedBundle.get_next_bundle')
    def test_not_call_last_used_bundle_when_bundles_is_1(self, next_mock, next_infra_mock):
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, 0)
        self.assertEqual(next_infra_mock.call_count, 0)

    @patch('workflow.steps.redis.deploy.create_virtualmachines.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.redis.deploy.create_virtualmachines.LastUsedBundle.get_next_bundle')
    def test_call_last_used_bundle_when_bundles_more_than_one(self, next_mock, next_infra_mock):
        self.plan_attr.bundle_group.bundles.add(CloudStackBundleFactory.create())
        next_mock.return_value = self.plan_attr.bundle_group.bundles.first()
        next_infra_mock.return_value = self.plan_attr.bundle_group.bundles.last()
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, self.expected_next_count)
        self.assertEqual(next_infra_mock.call_count, self.expected_next_infra_count)


class CreateVirtualMachineRedisSentinelTestCase(CreateVirtualMachineRedisSingleTestCase):
    vm_quantity = 3
    expected_next_count = 2
    expected_instances_quantity = 5

    def setUp(self):
        super(CreateVirtualMachineRedisSentinelTestCase, self).setUp()
        self.plan_attr.offering_group.offerings.add(CloudStackOfferingFactory.create(weaker=True))


@patch('workflow.steps.mongodb.deploy.create_virtualmachines.get_credentials_for',
       new=MagicMock(side_effect=fake_get_credentials_for))
class CreateVirtualMachineMongoSingleTestCase(CreateVirtualMachineMySQLSingleTestCase):
    vm_quantity = 1
    create_class = CreateVirtualMachineMongodb
    cloudstack_provider_path = 'workflow.steps.mongodb.deploy.create_virtualmachines.CloudStackProvider'
    expected_next_infra_count = 1
    expected_next_count = 0

    @patch('workflow.steps.mongodb.deploy.create_virtualmachines.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.mongodb.deploy.create_virtualmachines.LastUsedBundle.get_next_bundle')
    def test_not_call_last_used_bundle_when_bundles_is_1(self, next_mock, next_infra_mock):
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, 0)
        self.assertEqual(next_infra_mock.call_count, 0)

    @patch('workflow.steps.mongodb.deploy.create_virtualmachines.LastUsedBundle.get_next_infra_bundle')
    @patch('workflow.steps.mongodb.deploy.create_virtualmachines.LastUsedBundle.get_next_bundle')
    def test_call_last_used_bundle_when_bundles_more_than_one(self, next_mock, next_infra_mock):
        self.plan_attr.bundle_group.bundles.add(CloudStackBundleFactory.create())
        next_mock.return_value = self.plan_attr.bundle_group.bundles.first()
        next_infra_mock.return_value = self.plan_attr.bundle_group.bundles.last()
        self._create_vm_workflow()

        self.assertEqual(next_mock.call_count, self.expected_next_count)
        self.assertEqual(next_infra_mock.call_count, self.expected_next_infra_count)


class CreateVirtualMachineMongoArbiterTestCase(CreateVirtualMachineMongoSingleTestCase):
    vm_quantity = 3
    expected_next_count = 2

    def setUp(self):
        super(CreateVirtualMachineMongoArbiterTestCase, self).setUp()
        self.plan_attr.offering_group.offerings.add(CloudStackOfferingFactory.create(weaker=True))
