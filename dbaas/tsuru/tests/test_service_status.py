# -*- coding: utf-8 -*-
from mock import patch
from mock import Mock
import json

from django.test.client import Client
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response

from account.models import AccountUser, Role, Team, Organization
from logical.models import Database
from workflow.steps.util.base import ACLFromHellClient


@patch('workflow.steps.util.base.ACLFromHellClient.remove_acl')
@patch('tsuru.views.serviceAppBind.check_database_status')
class ServiceStatusTestCase(TestCase):
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.organization = Organization.objects.get_or_create(
            name='fake_organization')[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role,
            organization=self.organization)[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME, email="%s@admin.com" % self.USERNAME,
            password=self.PASSWORD)
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def test_get_service_status(
         self, mock_check_database_status, mock_acl_from_hell):
        mock_database = Mock(spec=Database)
        mock_check_database_status.return_value = Mock(spec=Database)
        mock_acl_from_hell.return_value = None

        mock_database.status = Database.ALIVE

        url = reverse('tsuru:service-status', args=('dev', 'test_database'))
        response = self.client.get(
            url, content_type='application/json')

        self.assertEquals(response.status_code, 204)
