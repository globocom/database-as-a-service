# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase
from django.core import mail
from account.tests.factory import TeamFactory
from logical.tests.factory import DatabaseFactory
from system.models import Configuration
from notification.tasks import database_notification_for_team


class TasksTestCase(TestCase):

    def setUp(self):
        self.team = TeamFactory()
        self.threshold_database_notification = Configuration(
            name='threshold_database_notification', value=70,
            description='Threshold infra notification'
        )
        self.threshold_database_notification.save()
        self.new_user_notify_email = Configuration(
            name='new_user_notify_email', value='me@email.com',
            description='New user notify e-mail'
        )
        self.new_user_notify_email.save()

        self.database_big = DatabaseFactory()
        self.database_big.team = self.team
        self.database_big.used_size_in_bytes = 9 * 1024 * 1024
        self.database_big.save()

        self.infra_big = self.database_big.databaseinfra
        self.infra_big.per_database_size_mbytes = 10
        self.infra_big.save()

        self.database_small = DatabaseFactory()
        self.database_small.team = self.team
        self.database_small.per_database_size_mbytes = 1 * 1024 * 1024
        self.database_small.save()

        self.infra_small = self.database_small.databaseinfra
        self.infra_small.per_database_size_mbytes = 10
        self.infra_small.save()

    def test_team_can_receive_notification(self):
        database_notification_for_team(team=self.team)
        self.assertEqual(len(mail.outbox), 2)

    def test_team_do_not_want_receive_notification(self):
        self.database_big.subscribe_to_email_events = False
        self.database_big.save()

        database_notification_for_team(team=self.team)
        self.assertEqual(len(mail.outbox), 0)
