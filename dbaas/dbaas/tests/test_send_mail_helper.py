from __future__ import absolute_import

from mock import patch, MagicMock
from django.core import mail

from util.tests.test_email_notification.base import EmailBaseTest


SUBJECT_TASK_SCHEDULE_CREATED = (
    '[DBaaS] Automatic Task created for Database {}'
)
SUBJECT_TASK_SCHEDULE_UPDATED = (
    '[DBaaS] Automatic Task updated for Database {}'
)
SUBJECT_TASK_SCHEDULE_EXECUTION_WARNING = (
    '[DBaaS] Automatic Task execution warning for Database {}'
)


class SubjectUpdateSSLTestCase(EmailBaseTest):
    action = 'update_ssl'

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_rigth_subject_when_is_new(self):

        self.task_schedule.send_mail(
            is_new=True,
            is_execution_warning=False
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

        self.task_schedule.send_mail(
            is_new=False,
            is_execution_warning=False
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

        self.task_schedule.send_mail(
            is_new=False,
            is_execution_warning=True
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


class SubjectRestartDatabaseTestCase(SubjectUpdateSSLTestCase):
    action = 'restart_database'


class BodyUpdateSSLTestCase(EmailBaseTest):

    action = 'update_ssl'
    expected_new_task_msg = ('The SSL of database fake_db_name is about '
                             'to expire')
    expected_update_task_msg = ('The schedule task of database fake_db_name '
                                'was changed')
    expected_execution_warn_task_msg = ("Update of fake_db_name&#39;s SSL "
                                        "certificate will be executed "
                                        "within 24 hours.")
    expected_available_msg = ('Do not worry about that, the database WILL BE '
                              'available during this process.')
    expected_unavailable_msg = ('The database WILL BE unavailable during this '
                                'process.')

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_new_task_message(self):

        self.task_schedule.send_mail(
            is_new=True,
            is_execution_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            self.expected_new_task_msg,
            mail.outbox[0].body,
        )
        self.assertIn(
            self.expected_new_task_msg,
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_updated_task_message(self):

        self.task_schedule.send_mail(
            is_new=False,
            is_execution_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            self.expected_update_task_msg,
            mail.outbox[0].body,
        )
        self.assertIn(
            self.expected_update_task_msg,
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_has_execution_warning_task_message(self):

        self.task_schedule.send_mail(
            is_new=False,
            is_execution_warning=True
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            self.expected_execution_warn_task_msg,
            mail.outbox[0].body,
        )
        self.assertIn(
            self.expected_execution_warn_task_msg,
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_available_msg_when_is_ha(self):
        self.database.infra.plan.is_ha = True
        self.database.infra.plan.save()
        self.task_schedule.send_mail(
            is_new=True,
            is_execution_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            self.expected_available_msg,
            mail.outbox[0].body,
        )
        self.assertIn(
            self.expected_available_msg,
            mail.outbox[1].body,
        )

    @patch('physical.models.DatabaseInfra.earliest_ssl_expire_at', MagicMock())
    def test_body_unavailable_msg_when_not_is_ha(self):
        self.database.infra.plan.is_ha = False
        self.database.infra.plan.save()
        self.task_schedule.send_mail(
            is_new=True,
            is_execution_warning=False
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(
            self.expected_unavailable_msg,
            mail.outbox[0].body,
        )
        self.assertIn(
            self.expected_unavailable_msg,
            mail.outbox[1].body,
        )


class BodyRestartDatabaseTestCase(BodyUpdateSSLTestCase):
    action = 'restart_database'
    expected_new_task_msg = 'The database fake_db_name needs to be restarted.'
    expected_update_task_msg = ('The schedule task of database fake_db_name '
                                'was changed')
    expected_execution_warn_task_msg = ("The Restart of fake_db_name will be "
                                        "executed within 24 hours.")
