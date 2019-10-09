# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib import admin
from ..admin.database_change_parameter import DatabaseChangeParameterAdmin
from ..models import DatabaseChangeParameter
from .factory import DatabaseChangeParameterFactory


SEARCH_FIELDS = ("database__name", "task__id", "task__task_id")
LIST_FILTER = [
    "database__team", "status",
]
LIST_DISPLAY = (
    "database", "database_team",
    "current_step", "friendly_status", "maintenance_action", "link_task",
    "started_at", "finished_at"
)
READONLY_FIELDS = (
    "database", "link_task", "started_at",
    "finished_at", "current_step", "status", "maintenance_action"
)
EXCLUDE = ("task", "can_do_retry")
ORDERING = ["-started_at"]
ACTIONS = None
LIST_SELECT_RELATED = None
NO_ACTION = 'N/A'


class DatabaseChangeParameterTestCase(TestCase):

    def setUp(self):
        self.database_change_parameter = DatabaseChangeParameterFactory()
        self.admin = DatabaseChangeParameterAdmin(
            DatabaseChangeParameter, admin.sites.AdminSite()
        )

    def tearDown(self):
        self.database_change_parameter.delete()

    def test_search_fields(self):
        self.assertEqual(SEARCH_FIELDS, self.admin.search_fields)

    def test_list_fields(self):
        self.assertEqual(LIST_FILTER, self.admin.list_filter)

    def test_list_display(self):
        self.assertEqual(LIST_DISPLAY, self.admin.list_display)

    def test_readonly_fields(self):
        self.assertEqual(READONLY_FIELDS, self.admin.readonly_fields)

    def test_exclude(self):
        self.assertEqual(EXCLUDE, self.admin.exclude)

    def test_ordering(self):
        self.assertEqual(ORDERING, self.admin.ordering)

    def test_actions(self):
        self.assertEqual(ACTIONS, self.admin.actions)

    def test_list_select_related(self):
        self.assertEqual(LIST_SELECT_RELATED, self.admin.list_select_related)

    def test_cannot_add(self):
        self.assertFalse(self.admin.has_add_permission(None))

    def test_cannot_delete(self):
        self.assertFalse(self.admin.has_delete_permission(None))

    def test_friendly_status_waiting(self):
        self.database_change_parameter.status = DatabaseChangeParameter.WAITING
        status_html = self.admin.friendly_status(
            self.database_change_parameter
        )
        self.assertIn('label-warning', status_html)
        self.assertIn('Waiting', status_html)

    def test_friendly_status_running(self):
        self.database_change_parameter.status = DatabaseChangeParameter.RUNNING
        status_html = self.admin.friendly_status(
            self.database_change_parameter
        )
        self.assertIn('label-success', status_html)
        self.assertIn('Running', status_html)

    def test_friendly_status_error(self):
        self.database_change_parameter.status = DatabaseChangeParameter.ERROR
        status_html = self.admin.friendly_status(
            self.database_change_parameter
        )
        self.assertIn('label-important', status_html)
        self.assertIn('Error', status_html)

    def test_friendly_status_success(self):
        self.database_change_parameter.status = DatabaseChangeParameter.SUCCESS
        status_html = self.admin.friendly_status(
            self.database_change_parameter
        )
        self.assertIn('label-info', status_html)
        self.assertIn('Success', status_html)

    def test_database_team(self):
        database_team = self.database_change_parameter.database.team.name
        admin_team = self.admin.database_team(self.database_change_parameter)
        self.assertEqual(database_team, admin_team)

    def test_link_task(self):
        admin_task = self.admin.link_task(self.database_change_parameter)
        self.assertIn(str(self.database_change_parameter.task.id), admin_task)

    def test_maintenance_action(self):
        self.database_change_parameter.status = DatabaseChangeParameter.ERROR
        url = (self.database_change_parameter.database
               .get_change_parameters_retry_url())

        button = self.admin.maintenance_action(self.database_change_parameter)
        self.assertIn(url, button)

    def test_maintenance_action_without_error_and_cannot_do_retry(self):
        self.database_change_parameter.status = DatabaseChangeParameter.SUCCESS
        self.database_change_parameter.can_do_retry = False
        button = self.admin.maintenance_action(self.database_change_parameter)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_with_error_and_cannot_do_retry(self):
        self.database_change_parameter.status = DatabaseChangeParameter.ERROR
        self.database_change_parameter.can_do_retry = False
        button = self.admin.maintenance_action(self.database_change_parameter)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_without_error_and_can_do_retry(self):
        self.database_change_parameter.status = DatabaseChangeParameter.SUCCESS
        self.database_change_parameter.can_do_retry = True
        button = self.admin.maintenance_action(self.database_change_parameter)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_with_error_and_can_do_retry(self):
        self.database_change_parameter.status = DatabaseChangeParameter.ERROR
        self.database_change_parameter.can_do_retry = True

        url = (self.database_change_parameter
               .database.get_change_parameters_retry_url())
        button = self.admin.maintenance_action(self.database_change_parameter)
        self.assertIn(url, button)
