# -*- coding: utf-8 -*-
from mock import patch
from mock import Mock

from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response

from account.models import Role, Team, Organization
from logical.models import Database


@patch('tsuru.views.ServiceAppBind.add_acl_for_hosts')
@patch('tsuru.views.check_database_status')
class ServiceAppBindPostTestCase(TestCase):
    """HTTP test cases for the tsuru bind API. This class focuses on the POST
    method.
    """
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.organization = Organization.objects.get_or_create(
            name='fake_organization'
        )[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role,
            organization=self.organization)[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME,
            email="{}@admin.com".format(self.USERNAME),
            password=self.PASSWORD
        )
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def test_user_is_authenticated(self, mock_check_database_status,
                                   mock_add_acl_for_hosts):
        """It tests user is authenticated."""
        mock_check_database_status.return_value = Response(
            {}, status=status.HTTP_200_OK
        )
        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        self.assertEquals(response.status_code, 200)

    def test_user_login_invalid(self, mock_check_database_status,
                                mock_add_acl_for_hosts):
        """It tests user is not authenticated."""
        client = Client()
        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = client.post(url, {'app-name': 'test-app'})

        self.assertEquals(response.status_code, 401)

    def test_redis_engine_without_sentinel(self, mock_check_database_status,
                                           mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal redis. It
        must return the env_vars to a redis without sentinel, wheater it is
        single or cluster configuration.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_redis_host', 8000
            ],
            'databaseinfra.engine.name': 'redis',
            'databaseinfra.password': 'test_password',
            'get_endpoint_dns.return_value': 'test.com:<password>',
            'infra.get_driver.return_value.topology_name.return_value': [
                'redis_single'
            ]
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        expected_data = {'DBAAS_REDIS_PASSWORD': 'test_password',
                         'DBAAS_REDIS_PORT': '8000',
                         'DBAAS_REDIS_HOST': 'test_redis_host',
                         'DBAAS_REDIS_ENDPOINT': 'test.com:test_password'}

        self.assertEquals(response.data, expected_data)
        self.assertEquals(response.status_code, 201)

    def test_redis_engine_with_sentinel(self, mock_check_database_status,
                                        mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal redis. It
        must return the env_vars to a redis sentinel.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_redis_host', 8000
            ],
            'databaseinfra.engine.name': 'redis',
            'databaseinfra.password': 'test_password',
            'get_endpoint_dns.return_value': 'test.com:<password>',
            'infra.get_driver.return_value.topology_name.return_value': [
                'redis_sentinel'
            ],
            'get_endpoint_dns_simple.return_value': 'cluster',
            'databaseinfra.name': 'test_infra'
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        expected_data = {
            'DBAAS_SENTINEL_PASSWORD': 'test_password',
            'DBAAS_SENTINEL_ENDPOINT': 'test.com:test_password',
            'DBAAS_SENTINEL_ENDPOINT_SIMPLE': 'cluster',
            'DBAAS_SENTINEL_SERVICE_NAME': 'test_infra',
            'DBAAS_SENTINEL_HOSTS': 'test_redis_host',
            'DBAAS_SENTINEL_PORT': '8000'
        }

        self.assertEquals(response.data, expected_data)
        self.assertEquals(response.status_code, 201)

    def test_mysql_engine(self, mock_check_database_status,
                          mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal mysql. It
        must return the env_vars to a mysql.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_mysql_hosts', 8000
            ],
            'databaseinfra.engine.name': 'mysql',
            'credentials.filter.return_value': [],
            'credentials.all.return_value': [
                Mock(user='test_mysql', password='test_password')
            ],
            'get_endpoint_dns.return_value': 'mysql:test.com:<user>:<password>'
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        expected_data = {
            "DBAAS_MYSQL_USER": 'test_mysql',
            "DBAAS_MYSQL_PASSWORD": 'test_password',
            "DBAAS_MYSQL_ENDPOINT": 'mysql:test.com:test_mysql:test_password',
            "DBAAS_MYSQL_HOSTS": 'test_mysql_hosts',
            "DBAAS_MYSQL_PORT": '8000'
        }

        self.assertEquals(response.data, expected_data)
        self.assertEquals(response.status_code, 201)

    def test_mongodb_engine(self, mock_check_database_status,
                            mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal mongodb. It
        must return the env_vars to a mongodb.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_mongodb_hosts', 8000
            ],
            'databaseinfra.engine.name': 'mongodb',
            'credentials.filter.return_value': [],
            'credentials.all.return_value': [
                Mock(user='test_mongodb', password='test_password')
            ],
            'get_endpoint_dns.return_value': (
                'mongodb:test.com:<user>:<password>'
            )
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        expected_data = {
            "DBAAS_MONGODB_USER": 'test_mongodb',
            "DBAAS_MONGODB_PASSWORD": 'test_password',
            "DBAAS_MONGODB_ENDPOINT": ('mongodb:test.com:test_mongodb:'
                                       'test_password'),
            "DBAAS_MONGODB_HOSTS": 'test_mongodb_hosts',
            "DBAAS_MONGODB_PORT": '8000'
        }

        self.assertEquals(response.data, expected_data)
        self.assertEquals(response.status_code, 201)


    def test_mongodb_engine_with_owner_user(self, mock_check_database_status,
                                            mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal mongodb. It
        must return the env_vars to a mongodb.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_mongodb_hosts', 8000
            ],
            'databaseinfra.engine.name': 'mongodb',
            'credentials.filter.return_value': [
                Mock(user='owner_mongodb', password='owner_password')
            ],
            'credentials.all.return_value': [
                Mock(user='test_mongodb', password='test_password')
            ],
            'get_endpoint_dns.return_value': (
                'mongodb:test.com:<user>:<password>'
            )
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        expected_data = {
            "DBAAS_MONGODB_USER": 'owner_mongodb',
            "DBAAS_MONGODB_PASSWORD": 'owner_password',
            "DBAAS_MONGODB_ENDPOINT": ('mongodb:test.com:owner_mongodb'
                                       ':owner_password'),
            "DBAAS_MONGODB_HOSTS": 'test_mongodb_hosts',
            "DBAAS_MONGODB_PORT": '8000'
        }

        self.assertEquals(response.data, expected_data)
        self.assertEquals(response.status_code, 201)

    def test_database_empty_credentials(self, mock_check_database_status,
                                        mock_add_acl_for_hosts):
        """ It tests if database.databaseinfra.engine.name is equal mysql. It
        must return the env_vars to a mysql.
        """
        mock_add_acl_for_hosts.return_value = None
        mock_database = Mock(spec=Database)
        attrs = {
            'infra.get_driver.return_value.get_dns_port.return_value': [
                'test_mysql_hosts', 8000
            ],
            'databaseinfra.engine.name': 'mysql',
            'credentials.filter.return_value': [],
            'credentials.all.return_value': [],
            'get_endpoint_dns.return_value': 'mysql:test.com:<user>:<password>'
        }
        mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = mock_database

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.post(url, {'app-name': 'test-app'})

        self.assertEquals(response.status_code, 500)
