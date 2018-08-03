from mock import MagicMock
from django.test import TestCase
from physical.models import Host
from physical.tests.factory import InstanceFactory, HostFactory
from logical.tests.factory import DatabaseFactory
from api.host import HostAPI


class HostTestCase(TestCase):
    def setUp(self):
        self.host_api = HostAPI()
        self.host_api.request = MagicMock()
        self.instance = InstanceFactory.create()

        self.instance.databaseinfra.databases.add(
            DatabaseFactory.create(databaseinfra=self.instance.databaseinfra)
        )

    def _validate_queryset(self, queryset):
        self.assertListEqual(
            list(Host.objects.filter(id=self.instance.hostname.id)),
            list(queryset)
        )

    def test_exclude_host_with_no_instances(self):
        HostFactory.create()
        queryset = self.host_api.get_queryset()

        self._validate_queryset(queryset)

    def test_exclude_host_with_no_database(self):
        InstanceFactory.create(address='fake_address02')

        queryset = self.host_api.get_queryset()

        self._validate_queryset(queryset)
