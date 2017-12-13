# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib import admin
from ..admin.database_upgrade import DatabaseUpgradeAdmin
from ..models import DatabaseUpgrade
from .factory import DatabaseUpgradeFactory


SEARCH_FIELDS = ("database__name", "task__id", "task__task_id")
LIST_FILTER = [
    "database__team", "source_plan", "target_plan", "source_plan__engine",
    "status",
]
LIST_DISPLAY = (
    "database", "database_team", "source_plan_name", "target_plan_name",
    "current_step", "friendly_status", "maintenance_action", "link_task",
    "started_at", "finished_at"
)
READONLY_FIELDS = (
    "database", "source_plan", "source_plan_name", "target_plan",
    "target_plan_name", "link_task", "started_at", "finished_at",
    "current_step", "status", "maintenance_action"
)
EXCLUDE = ("task", "can_do_retry")
ORDERING = ["-started_at"]
ACTIONS = None
LIST_SELECT_RELATED = None
NO_ACTION = 'N/A'


class DatabaseUpgradeTestCase(TestCase):

    def setUp(self):
        self.database_upgrade = DatabaseUpgradeFactory()
        self.admin = DatabaseUpgradeAdmin(
            DatabaseUpgrade, admin.sites.AdminSite()
        )

    def tearDown(self):
        self.database_upgrade.delete()

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
        self.database_upgrade.status = DatabaseUpgrade.WAITING
        status_html = self.admin.friendly_status(self.database_upgrade)
        self.assertIn('label-warning', status_html)
        self.assertIn('Waiting', status_html)

    def test_friendly_status_running(self):
        self.database_upgrade.status = DatabaseUpgrade.RUNNING
        status_html = self.admin.friendly_status(self.database_upgrade)
        self.assertIn('label-success', status_html)
        self.assertIn('Running', status_html)

    def test_friendly_status_error(self):
        self.database_upgrade.status = DatabaseUpgrade.ERROR
        status_html = self.admin.friendly_status(self.database_upgrade)
        self.assertIn('label-important', status_html)
        self.assertIn('Error', status_html)

    def test_friendly_status_success(self):
        self.database_upgrade.status = DatabaseUpgrade.SUCCESS
        status_html = self.admin.friendly_status(self.database_upgrade)
        self.assertIn('label-info', status_html)
        self.assertIn('Success', status_html)

    def test_database_team(self):
        database_team = self.database_upgrade.database.team.name
        admin_team = self.admin.database_team(self.database_upgrade)
        self.assertEqual(database_team, admin_team)

    def test_link_task(self):
        admin_task = self.admin.link_task(self.database_upgrade)
        self.assertIn(str(self.database_upgrade.task.id), admin_task)

    def test_maintenance_action(self):
        self.database_upgrade.status = DatabaseUpgrade.ERROR
        url = self.database_upgrade.database.get_upgrade_retry_url()

        button = self.admin.maintenance_action(self.database_upgrade)
        self.assertIn(url, button)

    def test_maintenance_action_without_error_and_cannot_do_retry(self):
        self.database_upgrade.status = DatabaseUpgrade.SUCCESS
        self.database_upgrade.can_do_retry = False
        button = self.admin.maintenance_action(self.database_upgrade)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_with_error_and_cannot_do_retry(self):
        self.database_upgrade.status = DatabaseUpgrade.ERROR
        self.database_upgrade.can_do_retry = False
        button = self.admin.maintenance_action(self.database_upgrade)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_without_error_and_can_do_retry(self):
        self.database_upgrade.status = DatabaseUpgrade.SUCCESS
        self.database_upgrade.can_do_retry = True
        button = self.admin.maintenance_action(self.database_upgrade)
        self.assertEqual(NO_ACTION, button)

    def test_maintenance_action_with_error_and_can_do_retry(self):
        self.database_upgrade.status = DatabaseUpgrade.ERROR
        self.database_upgrade.can_do_retry = True

        url = self.database_upgrade.database.get_upgrade_retry_url()
        button = self.admin.maintenance_action(self.database_upgrade)
        self.assertIn(url, button)

    def test_model_save_plan_name(self):
        self.assertGreater(self.database_upgrade.id, 0)
        self.assertIsNotNone(self.database_upgrade.source_plan)
        self.assertEqual(
            self.database_upgrade.source_plan.name,
            self.database_upgrade.source_plan_name
        )
        self.assertIsNotNone(self.database_upgrade.target_plan)
        self.assertEqual(
            self.database_upgrade.target_plan.name,
            self.database_upgrade.target_plan_name
        )

    def test_model_do_not_save_plan_name(self):
        self.assertEqual(
            self.database_upgrade.source_plan.name,
            self.database_upgrade.source_plan_name
        )
        self.database_upgrade.source_plan = None

        self.assertEqual(
            self.database_upgrade.target_plan.name,
            self.database_upgrade.target_plan_name
        )
        self.database_upgrade.target_plan = None

        self.assertGreater(self.database_upgrade.id, 0)
        self.database_upgrade.save()

        self.assertIsNotNone(self.database_upgrade.source_plan_name)
        self.assertIsNotNone(self.database_upgrade.target_plan_name)
