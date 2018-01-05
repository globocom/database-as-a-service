from django.test import TestCase
from physical.tests.factory import PlanFactory, DatabaseInfraFactory, InstanceFactory


class TestBaseStep(TestCase):

    def setUp(self):
        self.plan = PlanFactory()
        self.environment = self.plan.environments.first()
        self.infra = DatabaseInfraFactory(plan=self.plan, environment=self.environment)
        self.instance = InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=self.infra
        )

    def tearDown(self):
        self.instance.delete()
        self.infra.delete()
        self.environment.delete()
        self.plan.delete()
