from __future__ import absolute_import
from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core import mail
from system.models import Configuration
from account.tests.factory import TeamFactory
from physical.tests.factory import DiskOfferingFactory
from logical.tests.factory import DatabaseFactory
from util.email_notifications import get_domain, email_from, email_to, \
    disk_resize_notification

SUBJECT_DISK_RESIZE = '[DBaaS] Database {} auto disk resize to {}'


class DiskResizeTestCase(TestCase):

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
        self.team = TeamFactory()

    def test_can_get_domain(self):
        my_domain = Site.objects.get(id=1).domain
        self.assertNotIn('http://', my_domain)

        new_domain = get_domain()
        self.assertIn('http://', new_domain)

    def test_can_get_email_from(self):
        self.assertEqual(self.email_from.value, email_from())

    def test_can_get_email_to(self):
        self.assertEqual(self.email_adm.value, email_to(team=None))

    def test_can_get_email_to_with_team(self):
        expected_emails = [self.team.email, self.email_adm.value]
        self.assertEqual(expected_emails, email_to(team=self.team))

    def test_can_get_email_to_with_team_without_email(self):
        self.team.email = ''
        self.assertEqual(self.email_adm.value, email_to(self.team))

    def test_can_send_email_disk_resize(self):
        database = DatabaseFactory()
        new_disk = DiskOfferingFactory()
        usage_percentage = 76.89

        disk_resize_notification(
            database=database, new_disk=new_disk,
            usage_percentage=usage_percentage
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_DISK_RESIZE.format(database, new_disk)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_DISK_RESIZE.format(database, new_disk)
        )
