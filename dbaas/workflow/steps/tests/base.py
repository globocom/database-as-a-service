from unittest import TestCase

from physical.tests.factory import InstanceFactory


class StepBaseTestCase(TestCase):
    step_class = None

    def setUp(self):
        self.instance = InstanceFactory.build()
        assert self.step_class is not None, "U must set step_class attr"
        self.step = self.step_class(self.instance)
