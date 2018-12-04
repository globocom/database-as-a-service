# coding: utf-8
from django.test import TestCase

from physical.models import Instance
from physical.tests import factory as physical_factory
from workflow.steps.util.host_provider import CreateVirtualMachine


__all__ = ('BaseCreateVirtualMachineTestCase',)


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
