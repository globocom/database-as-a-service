# coding: utf-8
# from unittest import TestCase
from django.test import TestCase
from django.conf import settings
from physical.models import Instance
from physical.tests import factory as factory_physical
from logical.tests import factory as factory_logical
from django.template import Template, Context
from lxml import html as lhtml
from _mysql_exceptions import OperationalError
from drivers.errors import DatabaseDoesNotExist, InvalidCredential


class CapacityBaseTestCase(TestCase):

    KB2GB_FACTOR = (1.0 * 1024 * 1024)
    BYTE2GB_FACTOR = (1.0 * 1024 * 1024 * 1024)

    @classmethod
    def setUpClass(cls):
        try:
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
            name='mysql'
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
        cls.instance = factory_physical.InstanceFactory(
            address="new_instance.localinstance",
            port=123, is_active=True,
            instance_type=Instance.MYSQL,
            databaseinfra=cls.databaseinfra,
            hostname=cls.hostname
        )
        cls.database = factory_logical.DatabaseFactory(
            name='test_db_1',
            databaseinfra=cls.databaseinfra,
        )
        cls.nfsaas_host_attr = factory_physical.NFSaaSHostAttr(
            host=cls.hostname,
            # nfsaas_size_kb=cls.database.total_size_in_kb,
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
        self._change_fields(used_database_size=0)

        rendered_progress_bar = self._render_templatetag('disk')
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

        self.assertNotEqual(rendered_progress_bar, '', 'Not bar html found, expected be found')

        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('19.90%', database_bar.attrib.get('style', ''))
        self.assertIn('80.10%', free_bar.attrib.get('style', ''))


class MemoryCapacityTestCase(CapacityBaseTestCase):

    def test_no_bar_when_obj_not_found_on_context(self):
        html = '{% load capacity %}'
        html += '{% render_detailed_capacity_html database memory %}'
        progress_bar = Template(html)
        rendered_progress_bar = progress_bar.render(Context({}))

        self.assertEqual('', rendered_progress_bar)

    def test_percent(self):

        self.databaseinfra.per_database_size_mbytes = 500
        self.databaseinfra.save()
        self.database.used_size_in_bytes = 400000000
        self.database.save()

        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('74.00%', database_bar.attrib.get('style', ''))
        self.assertIn('26.00%', free_bar.attrib.get('style', ''))

    def test_0_percent(self):
        self.nfsaas_host_attr.nfsaas_size_kb = 10 * self.KB2GB_FACTOR  # 10GB
        self.nfsaas_host_attr.nfsaas_used_size_kb = 0
        self.nfsaas_host_attr.save()
        self.database.used_size_in_bytes = 0
        self.database.save()

        rendered_progress_bar = self._render_templatetag('memory')
        root = lhtml.fromstring(rendered_progress_bar)
        labels = root.cssselect('.bar-label-container .bar-label')
        database_bar = root.cssselect('.bar.database-bar')[0]
        free_bar = root.cssselect('.bar.free-bar')[0]

        self.assertEqual(len(labels), 2)
        self.assertIn('0.00%', database_bar.attrib.get('style', ''))
        self.assertIn('0.00%', free_bar.attrib.get('style', ''))
