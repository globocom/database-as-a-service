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
    "database", "database_team", "source_plan", "target_plan",
    "current_step", "friendly_status", "link_task", "started_at",
    "finished_at"
)
READONLY_FIELDS = (
    "database", "source_plan", "target_plan", "task", "started_at",
    "finished_at", "current_step", "status"
)
ORDERING = ["-started_at"]
ACTIONS = None


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

    def test_ordering(self):
        self.assertEqual(ORDERING, self.admin.ordering)

    def test_actions(self):
        self.assertEqual(ACTIONS, self.admin.actions)

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
