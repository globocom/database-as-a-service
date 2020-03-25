from __future__ import absolute_import

from django.contrib.sites.models import Site
from django.core import mail
from model_mommy import mommy

from util.email_notifications import get_domain, email_from, email_to, \
    disk_resize_notification
from .base import EmailBaseTest
from physical.models import DiskOffering


__all__ = ('DiskResizeTestCase',)


SUBJECT_DISK_AUTO_RESIZE = '[DBaaS] Database {} auto disk resize to {}'
SUBJECT_DISK_FINAL_AUTO_RESIZE = (
    '[DBaaS] Database {} final auto disk resize to {}'
)


class DiskResizeTestCase(EmailBaseTest):

    def setUp(self):
        DiskOffering.objects.all().delete()
        super(DiskResizeTestCase, self).setUp()
        self.greater_disk = mommy.make(
            'DiskOffering',
            size_kb=200
        )

        self.disk = mommy.make(
            'DiskOffering',
            size_kb=100
        )

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

    def test_can_send_email_disk_auto_resize(self):
        usage_percentage = 76.89

        disk_resize_notification(
            database=self.database, new_disk=self.disk,
            usage_percentage=usage_percentage
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_DISK_AUTO_RESIZE.format(self.database, self.disk)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_DISK_AUTO_RESIZE.format(self.database, self.disk)
        )

    def test_can_send_email_disk_final_auto_resize(self):
        usage_percentage = 76.89

        disk_resize_notification(
            database=self.database, new_disk=self.greater_disk,
            usage_percentage=usage_percentage
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_DISK_FINAL_AUTO_RESIZE.format(
                self.database, self.greater_disk
            )
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_DISK_FINAL_AUTO_RESIZE.format(
                self.database, self.greater_disk
            )
        )
