# coding: utf-8
# from unittest import TestCase
from mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django.template import Template, Context
from lxml import html as lhtml
from _mysql_exceptions import OperationalError

from physical.models import Instance
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from dbaas.tests.helpers import InstanceHelper
from drivers.errors import DatabaseDoesNotExist, InvalidCredential


class CapacityBaseTestCase(TestCase):

    KB2GB_FACTOR = MB2BYTE_FACTOR = (1.0 * 1024 * 1024)
    BYTE2GB_FACTOR = (1.0 * 1024 * 1024 * 1024)
    ENGINE = 'mysql'
    instance_helper = InstanceHelper
    instances_quantity = 1

    @classmethod
    def setUpClass(cls):
        try:
            with patch('drivers.fake.FakeDriver.check_instance_is_master',
                       new=MagicMock(side_effect=cls.instance_helper.check_instance_is_master)):
                cls._create_database_structure()
        except Exception, e:
            cls.clean_database()
            assert False, "{}".format(e)

    @classmethod
    def tearDownClass(cls):
        cls.clean_database()

    @classmethod
    def _create_database_structure(cls):
        mysql_host = settings.DB_HOST
        mysql_port = settings.DB_PORT or 3306
        cls.mysql_endpoint = '{}:{}'.format(mysql_host, mysql_port)
        cls.engine_type = factory_physical.EngineTypeFactory(
            name=cls.ENGINE
        )
        cls.engine = factory_physical.EngineFactory(
            engine_type=cls.engine_type
        )
        cls.disk_offering = factory_physical.DiskOfferingFactory(
            size_kb=524288
        )
        cls.plan = factory_physical.PlanFactory(
            disk_offering=cls.disk_offering,
            engine=cls.engine
        )
        cls.databaseinfra = factory_physical.DatabaseInfraFactory(
            name="__test__ mysqlinfra2",
            user="root", password=settings.DB_PASSWORD,
            endpoint=cls.mysql_endpoint,
            engine=cls.engine,
            disk_offering=cls.disk_offering,
            plan=cls.plan)
        cls.hostname = factory_physical.HostFactory()
        cls.instances = cls.instance_helper.create_instances_by_quant(
            instance_type=Instance.MYSQL, qt=cls.instances_quantity,
            infra=cls.databaseinfra, hostname=cls.hostname
        )
        cls.instance = cls.instances[0]
        cls.database = factory_logical.DatabaseFactory(
            name='test_db_1',
            databaseinfra=cls.databaseinfra,
        )
        cls.nfsaas_host_attr = factory_physical.NFSaaSHostAttr(
            host=cls.hostname,
            nfsaas_used_size_kb=cls.database.used_size_in_kb
        )

    @staticmethod
    def __remove_user(database):
        from logical.models import Credential
        from util import slugify
        credential = Credential()
        credential.database = database
        credential.user = 'u_{}'.format(database.name[:Credential.USER_MAXIMUM_LENGTH_NAME])
        credential.user = slugify(credential.user)
        try:
            credential.driver.remove_user(credential)
        except InvalidCredential:
            pass

    @classmethod
    def remove_field(cls, name, related=None):
        if hasattr(cls, name):
            field = getattr(cls, name)
            if related:
                related_field = getattr(field, related)
                related_field.all().delete()
            field.delete()

    @classmethod
    def clean_database(cls):
        from logical.models import Database
        databases = Database.objects.all()
        for database in databases:
            credentials = database.credentials.all()
            if credentials:
                for credential in credentials:
                    credential.delete()
            else:
                cls.__remove_user(database)
            try:
                database.delete()
            except (OperationalError, DatabaseDoesNotExist):
                pass

        cls.remove_field('nfsaas_host_attr')
        cls.remove_field('instance')
        cls.remove_field('hostname')
        cls.remove_field('databaseinfra', 'databases')
        cls.remove_field('plan')
        cls.remove_field('disk_offering')
        cls.remove_field('engine')
        cls.remove_field('engine_type')

    def _render_templatetag(self, bar_type):
        html = '{% load capacity %}'
        html += '{{% render_detailed_capacity_html database {} %}}'.format(bar_type)
        progress_bar = Template(html)
        return progress_bar.render(Context({
            'database': self.database}))


@patch('drivers.fake.FakeDriver.check_instance_is_master',
       new=MagicMock(side_effect=InstanceHelper.check_instance_is_master))
class DiskCapacityTestCase(CapacityBaseTestCase):

    def _change_fields(
            self, is_in_memory=False,
            total_disk_size=10,
            used_disk_size=5,
            has_persistence=True,
            used_database_size=2.5):

        self.plan.has_persistence = True
        self.plan.save()
        self.engine_type.is_in_memory = is_in_memory
        self.engine_type.save()
        self.nfsaas_host_attr.nfsaas_size_kb = total_disk_size * self.KB2GB_FACTOR
        self.nfsaas_host_attr.nfsaas_used_size_kb = used_disk_size * self.KB2GB_FACTOR if used_disk_size is not None else None
        self.nfsaas_host_attr.save()
        self.database.plan.has_persistence = has_persistence
        self.database.plan.save()
        self.database.used_size_in_bytes = used_database_size * self.BYTE2GB_FACTOR  # 2.5GB
        self.database.save()
        self.instance.total_size_in_bytes = total_disk_size * self.BYTE2GB_FACTOR
        self.instance.used_size_in_bytes = used_database_size * self.BYTE2GB_FACTOR
        self.instance.save()

    def test_no_bar_when_obj_not_found_on_context(self):
        html = '{% load capacity %}'
        html += '{% render_detailed_capacity_html database disk %}'
        progress_bar = Template(html)
        rendered_progress_bar = progress_bar.render(Context({}))

        self.assertEqual('', rendered_progress_bar)

    def test_percent(self):
        self._change_fields()
        rendered_progress_bar = self._render_templatetag('disk')

        root = lhtml.fromstring(rendered_progress_bar)
        database_bar = root.cssselect('.bar.database-bar')[0]
        other_bar = root.cssselect('.bar.other-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertIn('25.00%', database_bar.attrib.get('style', ''))
        self.assertIn('25.00%', other_bar.attrib.get('style', ''))
        self.assertIn('50.00%', free_bar.attrib.get('style', ''))

    def test_0_percent(self):
        self._change_fields(used_database_size=0, used_disk_size=0)

        rendered_progress_bar = self._render_templatetag('disk')

        self.assertNotEqual('', rendered_progress_bar, 'No bar found, expected to be found')

        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        other_bar = root.cssselect('.bar.other-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 3)
        self.assertIn('0.00%', database_bar.attrib.get('style', ''))
        self.assertIn('0.00%', other_bar.attrib.get('style', ''))
        self.assertIn('0.00%', free_bar.attrib.get('style', ''))

    def test_nfsaas_used_is_null(self):
        self._change_fields(
            is_in_memory=False,
            used_disk_size=None,
            used_database_size=0)
        rendered_progress_bar = self._render_templatetag('disk')

        self.assertEqual('', rendered_progress_bar)

    def test_database_in_memory_not_persisted(self):
        self._change_fields(
                is_in_memory=True,
                used_disk_size=0,
                has_persistence=False,
                used_database_size=0
        )

        rendered_progress_bar = self._render_templatetag('disk')

        self.assertEqual('', rendered_progress_bar)

    def test_database_in_memory_persisted(self):
        self._change_fields(
                is_in_memory=True,
                used_disk_size=None,
                has_persistence=True,
                used_database_size=1
        )

        rendered_progress_bar = self._render_templatetag('disk')

        self.assertEqual('', rendered_progress_bar)

    def test_database_in_memory_and_persisted(self):
        self._change_fields(
                is_in_memory=True,
                used_disk_size=9,
                has_persistence=True,
                used_database_size=1
        )

        rendered_progress_bar = self._render_templatetag('disk')

        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        used_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('90.00%', used_bar.attrib.get('style', ''))
        self.assertIn('10.00%', free_bar.attrib.get('style', ''))

    def test_in_memory_and_used_disk_none(self):
        '''
        The Bar must appear when the db is in memory and the used disk is None
        '''
        self._change_fields(
                is_in_memory=True,
                used_disk_size=None,
                used_database_size=1.9876
        )

        rendered_progress_bar = self._render_templatetag('disk')

        self.assertEqual(rendered_progress_bar, '')


@patch('drivers.fake.FakeDriver.check_instance_is_master',
       new=MagicMock(side_effect=InstanceHelper.check_instance_is_master))
class MemoryCapacityTestCase(CapacityBaseTestCase):

    def test_no_bar_when_obj_not_found_on_context(self):
        html = '{% load capacity %}'
        html += '{% render_detailed_capacity_html database memory %}'
        progress_bar = Template(html)
        rendered_progress_bar = progress_bar.render(Context({}))

        self.assertEqual('', rendered_progress_bar)

    def test_percent(self):

        def _update_instance(instance):
            instance.total_size_in_bytes = 10 * self.BYTE2GB_FACTOR
            instance.used_size_in_bytes = 7.45 * self.BYTE2GB_FACTOR
            instance.save()

        self.instances = map(_update_instance, self.instances)
        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('74.50%', database_bar.attrib.get('style', ''))
        self.assertIn('25.50%', free_bar.attrib.get('style', ''))

    def test_0_percent(self):
        self.nfsaas_host_attr.nfsaas_size_kb = 10 * self.KB2GB_FACTOR  # 10GB
        self.nfsaas_host_attr.nfsaas_used_size_kb = 0
        self.nfsaas_host_attr.save()
        self.instance.used_size_in_bytes = 0
        self.instance.total_size_in_bytes = 10 * self.BYTE2GB_FACTOR
        self.instance.save()

        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('0.00%', database_bar.attrib.get('style', ''))
        self.assertIn('0.00%', free_bar.attrib.get('style', ''))


class MemoryCapacityHATestCase(MemoryCapacityTestCase):
    instances_quantity = 2


@patch('drivers.fake.FakeDriver.check_instance_is_master',
       new=MagicMock(side_effect=InstanceHelper.check_instance_is_master))
class MemoryCapacityMultiMasterTestCase(CapacityBaseTestCase):

    instances_quantity = 6

    def _change_master(self, master, total_size_in_gb, used_size_in_gb):
        master.total_size_in_bytes = total_size_in_gb * self.BYTE2GB_FACTOR
        master.used_size_in_bytes = used_size_in_gb * self.BYTE2GB_FACTOR
        master.save()

    def _validate_bar(self, bar, expected_used_percent, expected_free_percent):
        labels = bar.cssselect('.bar-label-container .bar-label')
        database_bar = bar.cssselect('.bar.database-bar')[0]
        free_bar = bar.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn(expected_used_percent, database_bar.attrib.get('style', ''))
        self.assertIn(expected_free_percent, free_bar.attrib.get('style', ''))

    def test_no_bar_when_obj_not_found_on_context(self):
        html = '{% load capacity %}'
        html += '{% render_detailed_capacity_html database memory %}'
        progress_bar = Template(html)
        rendered_progress_bar = progress_bar.render(Context({}))

        self.assertEqual('', rendered_progress_bar)

    def test_percent(self):

        master_1, master_2, master_3 = self.databaseinfra.get_driver().get_master_instance()
        self._change_master(master_1, total_size_in_gb=10, used_size_in_gb=7.45)
        self._change_master(master_2, total_size_in_gb=10, used_size_in_gb=6.0)
        self._change_master(master_3, total_size_in_gb=10, used_size_in_gb=1.0)

        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        bars = root.cssselect('.memory-progress-bar')
        self.assertEqual(len(bars), 3)
        self._validate_bar(bars[0], '74.50%', '25.50%')
        self._validate_bar(bars[1], '60.00%', '40.00%')
        self._validate_bar(bars[2], '10.00%', '90.00%')

    def test_0_percent(self):
        self.nfsaas_host_attr.nfsaas_size_kb = 10 * self.KB2GB_FACTOR  # 10GB
        self.nfsaas_host_attr.nfsaas_used_size_kb = 0
        self.nfsaas_host_attr.save()
        master_1, master_2, master_3 = self.instances[:3]
        self._change_master(master_1, total_size_in_gb=10, used_size_in_gb=0)
        self._change_master(master_2, total_size_in_gb=10, used_size_in_gb=0)
        self._change_master(master_3, total_size_in_gb=10, used_size_in_gb=0)

        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        bars = root.cssselect('.memory-progress-bar')
        self.assertEqual(len(bars), 3)
        self._validate_bar(bars[0], '0.00%', '100.00%')
        self._validate_bar(bars[1], '0.00%', '100.00%')
        self._validate_bar(bars[2], '0.00%', '100.00%')
