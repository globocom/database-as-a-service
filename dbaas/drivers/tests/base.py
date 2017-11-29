from unittest import TestCase

from django.conf import settings

from physical.tests import factory as factory_physical
from physical.models import Instance
from logical.models import Database
from drivers.mysqldb import MySQL


class BaseDriverTestCase(TestCase):

    host = None
    port = None
    db_user = 'admin'
    db_password = '123456'
    engine_name = ''
    instance_type = None
    driver_class = None
    driver_client_lookup = ''

    def setUp(self):
        host = self.host or '127.0.0.1'
        port = self.port or 3306
        self.endpoint = "{}:{}".format(host, port)
        self.databaseinfra = factory_physical.DatabaseInfraFactory(
            password=self.db_password, endpoint=self.endpoint,
            engine__engine_type__name=self.engine_name, user=self.db_user
        )
        self.instance = factory_physical.InstanceFactory(
            databaseinfra=self.databaseinfra, port=port,
            instance_type=self.instance_type, address=host
        )
        self.driver = self.driver_class(databaseinfra=self.databaseinfra)
        self._driver_client = None

    def tearDown(self):
        Instance.objects.all().delete()
        if not Database.objects.filter(databaseinfra_id=self.databaseinfra.id):
            self.databaseinfra.delete()
        if self._driver_client:
            self.driver_client.close()
        # self.driver = self.databaseinfra = self._driver_client = None

    @property
    def driver_client(self):
        if self._driver_client is None:
            get_driver_func = getattr(
                self.driver, self.driver_client_lookup
            )
            self._driver_client = get_driver_func(self.instance)
        return self._driver_client


class BaseMysqlDriverTestCase(BaseDriverTestCase):

    host = settings.DB_HOST
    port = 3306
    db_user = 'root'
    db_password = settings.DB_PASSWORD
    engine_name = 'mysql'
    instance_type = 1
    driver_class = MySQL
    driver_client_lookup = '__mysql_client__'
