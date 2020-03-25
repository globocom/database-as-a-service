from django.test import TestCase
from mock import patch, MagicMock
from maintenance.models import task_schedule_post_save


__all__ = ('SendMailConfTestCase',)


@patch('maintenance.models.schedule_task_notification')
class SendMailConfTestCase(TestCase):
    @patch('system.models.Configuration.get_by_name',
           MagicMock(return_value=True))
    def test_send_mail_when_cofigured(self, schedule_notification_mock):
        task_schedule_post_save(sender=MagicMock(), instance=MagicMock())
        self.assertTrue(schedule_notification_mock.called)

    @patch('system.models.Configuration.get_by_name',
           MagicMock(return_value=False))
    def test_dont_send_mail_when_cofigured(self, schedule_notification_mock):
        task_schedule_post_save(sender=MagicMock(), instance=MagicMock())
        self.assertFalse(schedule_notification_mock.called)
