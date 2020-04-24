from __future__ import absolute_import

from django.test import TestCase
from django.core.cache import cache
from django.core import mail
from model_mommy import mommy

from system.models import Configuration
from dbaas.tests.helpers import DatabaseHelper


class EmailBaseTest(TestCase):
    action = 'update_ssl'

    def setUp(self):
        cache.clear()
        mail.outbox = []

        self.email_from = Configuration(
            name='email_addr_from', value='dbaas@mail.com'
        )
        self.email_from.save()

        self.email_adm = Configuration(
            name='new_user_notify_email', value='adm@mail.com'
        )
        self.email_adm.save()
        self.team = mommy.make(
            'Team',
            name='team_1',
            email='team_1@email.test.com',
            contacts='contact_1',
            role__name='fake_role',
            organization__name='fake_organization'
        )
        self.database = DatabaseHelper.create(
            name='fake_db_name', team=self.team
        )
        self.task_schedule = mommy.make(
            'TaskSchedule',
            method_path=self.action,
            database=self.database
        )
