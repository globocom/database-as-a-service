# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group
from ..models import AccountUser, Role, Team
from . import factory

LOG = logging.getLogger(__name__)


class AdminCreateDatabaseTestCase(TestCase):
    """ HTTP test cases """
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):

        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.team = Team.objects.get_or_create(name="fake_team", role=self.role)[0]
        self.superuser = User.objects.create_superuser(self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)


    def tearDown(self):
        self.client.logout()

    def test_user_is_authenticated(self):
        """
        Tests user is authenticated
        """
        response = self.client.get('/admin/auth/accountuser/')
        
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.index("Select user to change"), -1)

    def test_user_login_invalid(self):
        """
        Tests user is authenticated
        """
        client = Client()
        data = {'username': 'john', 'password': 'smith'}
        response = client.post('/admin/login/', data)
        self.assertNotEqual(response.content.index("Please enter the correct username and password"), -1)


