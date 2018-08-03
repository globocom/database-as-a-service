#from mock import patch
#from physical.tests.factory import HostFactory, EnvironmentFactory
#from ..util.vm import VmStep, MigrationWaitingBeReady
#from . import TestBaseStep
#
#
#@patch('workflow.steps.util.vm.get_credentials_for', return_value=True)
#@patch('workflow.steps.util.vm.CloudStackProvider', return_value=object)
#class VMStepTests(TestBaseStep):
#
#    def setUp(self):
#        super(VMStepTests, self).setUp()
#        self.host = self.instance.hostname
#
#    def test_environment(self, *args, **kwargs):
#        vm_step = VmStep(self.instance)
#        self.assertEqual(vm_step.environment, self.environment)
#
#    def test_host(self, *args, **kwargs):
#        vm_step = VmStep(self.instance)
#        self.assertEqual(vm_step.host, self.host)
#
#
#@patch('workflow.steps.util.vm.get_credentials_for', return_value=True)
#@patch('workflow.steps.util.vm.CloudStackProvider', return_value=object)
#class VMStepTestsMigration(TestBaseStep):
#
#    def setUp(self):
#        super(VMStepTestsMigration, self).setUp()
#
#        self.host = self.instance.hostname
#        self.future_host = HostFactory()
#        self.host.future_host = self.future_host
#        self.host.save()
#
#        self.environment_migrate = EnvironmentFactory()
#        self.environment.migrate_environment = self.environment_migrate
#        self.environment.save()
#
#    def test_environment(self, *args, **kwargs):
#        vm_step = MigrationWaitingBeReady(self.instance)
#        self.assertEqual(vm_step.environment, self.environment_migrate)
#
#    def test_host(self, *args, **kwargs):
#        vm_step = MigrationWaitingBeReady(self.instance)
#        self.assertEqual(vm_step.host, self.future_host)
