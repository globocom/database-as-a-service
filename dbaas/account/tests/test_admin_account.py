# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.core.urlresolvers import reverse
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
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role)[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def test_user_is_authenticated(self):
        """
        Tests user is authenticated
        """
        url = reverse('admin:account_accountuser_changelist')
        response = self.client.get(url)

        self.assertContains(
            response, "Select user to change",  status_code=200)

    def test_user_login_invalid(self):
        """
        Tests user is authenticated
        """
        client = Client()
        data = {'username': 'john', 'password': 'smith'}
        response = client.post('/admin/login/', data)
        self.assertContains(
            response, "Please enter the correct username and password",  status_code=200)

    def test_can_load_audit_page(self):
        """Test audit page load"""
        url = reverse('admin:simple_audit_audit_changelist')
        response = self.client.get(url)

        self.assertContains(
            response, "Select Audit to change",  status_code=200)

    def test_can_load_user_add_page(self):
        """Test user add page load"""
        url = reverse('admin:account_accountuser_add')
        response = self.client.get(url)

        self.assertContains(response, "Add user",  status_code=200)

    def test_can_load_user_edit_page(self):
        """Test user add page load"""
        url = reverse(
            'admin:account_accountuser_change', args=(self.superuser.id,))
        response = self.client.get(url)

        self.assertContains(response, "Change user",  status_code=200)
