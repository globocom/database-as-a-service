# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import mock
from django.test import TestCase
from django.contrib.auth.models import User
from drivers import fake, base
from physical.tests import factory as physical_factory
from ..models import Database
from ..forms import DatabaseForm
from . import factory

from account.models import Team, Role

LOG = logging.getLogger(__name__)


class AdminCreateDatabaseTestCase(TestCase):
    """ HTTP test cases """
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.plan = physical_factory.PlanFactory()
        self.environment = self.plan.environments.all()[0]
        self.databaseinfra = physical_factory.DatabaseInfraFactory(plan=self.plan, environment=self.environment, capacity=10)
        self.project = factory.ProjectFactory()
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.team = Team.objects.get_or_create(name="fake_team", role=self.role)[0]
        self.user = User.objects.create_superuser(self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.user)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.engine = None
        self.client.logout()

    def test_user_pass_all_arguments_and_database_is_created(self):
        database_name = "test_new_database"
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertEqual(response.status_code, 302, response.content)
        self.assertTrue(fake.database_created(self.databaseinfra.name, database_name))

        database = Database.objects.get(databaseinfra=self.databaseinfra, name=database_name)
        self.assertEqual(self.project, database.project)

    def test_try_create_a_new_database_but_database_already_exists(self):
        database_name = "test_new_database"
        self.database = factory.DatabaseFactory(databaseinfra=self.databaseinfra, name=database_name)
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn('this name already exists in the selected environment', response.content)

    @mock.patch.object(fake.FakeDriver, 'create_database')
    def test_try_create_a_new_database_but_database_already_exists_only_in_driver(self, create_database):
        create_database.side_effect = base.DatabaseAlreadyExists
        database_name = "test_new_database"
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue('already exists in infra-structure but not in DBaaS' in response.content, response.content)

    def test_db_name(self):
        data = {'name': '', 'project': 'any_project'}
        form = DatabaseForm(data=data)
        self.assertFalse(form.is_valid())

    def test_project_choice(self):
        data = {'name': 'some_name', 'project': ''}
        form = DatabaseForm(data=data)
        self.assertFalse(form.is_valid())

