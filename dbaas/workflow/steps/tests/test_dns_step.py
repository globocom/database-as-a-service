from random import randint
from django.test import TestCase
from mock import patch
from physical.tests.factory import PlanFactory, DatabaseInfraFactory, InstanceFactory
from workflow.steps.util.dns import ChangeTTL, ChangeTTLTo5Minutes, ChangeTTLTo3Hours



class FakeDNSProvider(object):

    dns_ttl = {}

    @classmethod
    def update_database_dns_ttl(cls, infra, seconds):
        cls.dns_ttl[infra] = seconds

class DNSStepTests(TestCase):

    def setUp(self):
        FakeDNSProvider.dns_ttl = {}
        plan = PlanFactory()
        environment = plan.environments.first()
        self.infra = DatabaseInfraFactory(plan=plan, environment=environment)
        self.instance = InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=self.infra
        )

    @patch(
        'dbaas_dnsapi.provider.DNSAPIProvider.update_database_dns_ttl',
        new=FakeDNSProvider.update_database_dns_ttl
    )
    def test_change_ttl_five_minutes(self):
        self.assertEqual(FakeDNSProvider.dns_ttl, {})
        ChangeTTLTo5Minutes(self.instance).do()

        self.assertEqual(len(FakeDNSProvider.dns_ttl), 1)
        self.assertIn(self.infra, FakeDNSProvider.dns_ttl)
        ttl_seconds = FakeDNSProvider.dns_ttl[self.infra]
        self.assertEqual(ttl_seconds, 300)

    @patch(
        'dbaas_dnsapi.provider.DNSAPIProvider.update_database_dns_ttl',
        new=FakeDNSProvider.update_database_dns_ttl
    )
    def test_change_ttl_3_hours(self):
        self.assertEqual(FakeDNSProvider.dns_ttl, {})
        ChangeTTLTo3Hours(self.instance).do()

        self.assertEqual(len(FakeDNSProvider.dns_ttl), 1)
        self.assertIn(self.infra, FakeDNSProvider.dns_ttl)
        ttl_seconds = FakeDNSProvider.dns_ttl[self.infra]
        self.assertEqual(ttl_seconds, 10800)

    def test_minutes_to_seconds(self):
        change_ttl = ChangeTTLTo5Minutes(self.instance)
        change_ttl.minutes = randint(1, 10000)
        self.assertEqual(change_ttl.seconds, change_ttl.minutes*60)

    def test_unicode(self):
        change_ttl = ChangeTTLTo5Minutes(self.instance)
        change_ttl.minutes = randint(1, 10000)
        self.assertEqual(
            unicode(change_ttl),
            'Changing DNS TLL to {} minutes...'.format(change_ttl.minutes)
        )
