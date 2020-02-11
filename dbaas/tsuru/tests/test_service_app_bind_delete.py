# -*- coding: utf-8 -*-
from mock import patch
from mock import Mock
import json

from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response

from account.models import Role, Team, Organization
from logical.models import Database


@patch('workflow.steps.util.base.ACLFromHellClient.remove_acl')
@patch('tsuru.views.check_database_status')
class ServiceAppBindDeleteTestCase(TestCase):
    """HTTP test cases for the tsuru unbind API. This class focuses on the
    DELETE method.
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
            organization=self.organization
        )[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME,
            email="%s@admin.com" % self.USERNAME,
            password=self.PASSWORD
        )
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def test_user_is_authenticated(
        self,
        mock_check_database_status,
        mock_acl_from_hell
    ):
        """It tests user is authenticated."""
        mock_check_database_status.return_value = Response(
            {},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.delete(
            url,
            json.dumps({'app-name': 'test-app'}),
            content_type='application/json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_user_login_invalid(
        self,
        mock_check_database_status,
        mock_acl_from_hell
    ):
        """It tests user is not authenticated."""
        client = Client()
        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = client.delete(url, {'app-name': 'test-app'})

        self.assertEquals(response.status_code, 401)

    def test_delete_204(self, mock_check_database_status, mock_acl_from_hell):
        """ It tests if database.databaseinfra.engine.name is equal mysql. It
        must return the env_vars to a mysql.
        """
        mock_database = Mock(spec=Database)
        print('instance:', isinstance(mock_database, Database))
        # attrs = {'environment': 'dev'}
        # mock_database.configure_mock(**attrs)
        mock_check_database_status.return_value = Mock(spec=Database)
        mock_acl_from_hell.return_value = None

        url = reverse('tsuru:service-app-bind', args=('dev', 'test_database'))
        response = self.client.delete(url, json.dumps(
            {'app-name': 'test-app'}),
            content_type='application/json'
        )

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
