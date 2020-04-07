from __future__ import absolute_import

from mock import patch, MagicMock
from django.core import mail

from util.email_notifications import schedule_task_notification
from .base import EmailBaseTest


__all__ = ('SubjectTestCase', 'BodyTestCase',)


SUBJECT_TASK_SCHEDULE_CREATED = (
    '[DBaaS] Automatic Task created for Database {}'
)
SUBJECT_TASK_SCHEDULE_UPDATED = (
    '[DBaaS] Automatic Task updated for Database {}'
)
SUBJECT_TASK_SCHEDULE_EXECUTION_WARNING = (
    '[DBaaS] Automatic Task execution warning for Database {}'
)


class SubjectTestCase(EmailBaseTest):

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_rigth_subject_when_is_new(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=True,
            is_task_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_TASK_SCHEDULE_CREATED.format(self.database)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_TASK_SCHEDULE_CREATED.format(self.database)
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_rigth_subject_when_updated(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=False,
            is_task_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_TASK_SCHEDULE_UPDATED.format(self.database)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_TASK_SCHEDULE_UPDATED.format(self.database)
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_rigth_subject_when_execution_warning(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=False,
            is_task_warning=True
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].subject,
            SUBJECT_TASK_SCHEDULE_EXECUTION_WARNING.format(self.database)
        )
        self.assertEqual(
            mail.outbox[1].subject,
            SUBJECT_TASK_SCHEDULE_EXECUTION_WARNING.format(self.database)
        )


class BodyTestCase(EmailBaseTest):

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_new_task_message(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=True,
            is_task_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            'The SSL of database fake_db_name is about to expire',
            mail.outbox[0].body,
        )
        self.assertIn(
            'The SSL of database fake_db_name is about to expire',
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_updated_task_message(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=False,
            is_task_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            'The schedule task of database fake_db_name was changed',
            mail.outbox[0].body,
        )
        self.assertIn(
            'The schedule task of database fake_db_name was changed',
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_execution_warning_task_message(self):

        schedule_task_notification(
            database=self.database,
            scheduled_task=MagicMock(),
            is_new=False,
            is_task_warning=True
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            ('The update of the SSL certificate of the database fake_db_name '
             'will be executed within 24 hours.'),
            mail.outbox[0].body,
        )
        self.assertIn(
            ('The update of the SSL certificate of the database fake_db_name '
             'will be executed within 24 hours.'),
            mail.outbox[1].body,
        )
