# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from django.contrib.auth.models import User
from physical.tests import factory as physical_factory
from account.models import Team, Role, Organization
from drivers import fake, base
from ..forms import DatabaseForm
from ..models import Database
from . import factory

LOG = logging.getLogger(__name__)


class AdminCreateDatabaseTestCase(TestCase):

    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.plan = physical_factory.PlanFactory()
        self.environment = self.plan.environments.all()[0]
        self.databaseinfra = physical_factory.DatabaseInfraFactory(
            plan=self.plan, environment=self.environment, capacity=10)
        self.instance = physical_factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=self.databaseinfra)
        self.project = factory.ProjectFactory()
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.organization = Organization.objects.get_or_create(name='fake_organization')[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role, database_alocation_limit=0,
            organization=self.organization)[0]
        self.user = User.objects.create_superuser(
            self.USERNAME, email="%s@admin.com" % self.USERNAME, password=self.PASSWORD)
        self.team.users.add(self.user)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.description = "My database"

    def tearDown(self):
        self.engine = None
        self.client.logout()

    def test_user_tries_to_create_database_without_team(self):
        database_name = "test_new_database_without_team"
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
            "description": self.description,
            "backup_hour": self.databaseinfra.backup_hour,
            "maintenance_window": self.databaseinfra.maintenance_window,
            "maintenance_day": self.databaseinfra.maintenance_day,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertContains(
            response, "Team: This field is required", status_code=200)

    def test_user_tries_to_create_database_without_description(self):
        database_name = "test_new_database_without_team"
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
            "team": self.team.pk,
            "backup_hour": self.databaseinfra.backup_hour,
            "maintenance_window": self.databaseinfra.maintenance_window,
            "maintenance_day": self.databaseinfra.maintenance_day,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertContains(
            response, "Description: This field is required.", status_code=200)

    def test_try_create_a_new_database_but_database_already_exists(self):
        database_name = "test_new_database"
        self.database = factory.DatabaseFactory(
            databaseinfra=self.databaseinfra, name=database_name)
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
            "team": self.team.pk,
            "description": self.description,
            "backup_hour": self.databaseinfra.backup_hour,
            "maintenance_window": self.databaseinfra.maintenance_window,
            "maintenance_day": self.databaseinfra.maintenance_day,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertContains(
            response, "this name already exists in the selected environment", status_code=200)

    def test_db_name(self):
        data = {'name': '', 'project': 'any_project'}
        form = DatabaseForm(data=data)
        self.assertFalse(form.is_valid())

    def test_project_choice(self):
        data = {'name': 'some_name', 'project': ''}
        form = DatabaseForm(data=data)
        self.assertFalse(form.is_valid())

    def test_user_pass_all_arguments_and_database_is_created(self):
        database_name = "test_new_database"
        params = {
            "name": database_name,
            "project": self.project.pk,
            "plan": self.plan.pk,
            "environment": self.environment.pk,
            "engine": self.databaseinfra.engine.pk,
            "team": self.team.pk,
            "description": self.description,
            "backup_hour": self.databaseinfra.backup_hour,
            "maintenance_window": self.databaseinfra.maintenance_window,
            "maintenance_day": self.databaseinfra.maintenance_day,
        }
        response = self.client.post("/admin/logical/database/add/", params)
        self.assertEqual(response.status_code, 302, response.content)

        database = fake.database_created_list(database_name)
        self.assertIsNotNone(database)
