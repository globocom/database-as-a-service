import copy
from mock import patch
from lxml import html as lhtml
from unittest import TestCase
from django.template import Template, Context
from .fakes.get_notifications import (THREE_TASKS_TWO_NEWS, THREE_TASKS_ZERO_NEWS,
                                      THREE_TASKS_THREE_NEWS)


class NotificationTagTestCase(TestCase):
    def setUp(self):
        html = '{% load notification_tags %}'
        html += '{% get_notifications user %}'
        self.notification = Template(html)

    def _render_notification(self):
        return lhtml.fromstring(self.notification.render(Context({'user': 'admin'})))

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=[])
    def test_no_notification(self, mock_get):
        notification = self._render_notification()
        no_notification_el = notification.cssselect('.no-notification')

        self.assertTrue(no_notification_el)
        self.assertEqual(no_notification_el[0].text_content().strip(), 'No tasks found.')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_ZERO_NEWS)
    def test_count_0(self, mock_get):
        notification = self._render_notification()
        notification_count_el = notification.cssselect('.notification-cnt')

        self.assertTrue(notification_count_el)
        self.assertEqual(notification_count_el[0].text_content().strip(), '0')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_TWO_NEWS)
    def test_count_2(self, mock_get):
        notification = self._render_notification()
        notification_count_el = notification.cssselect('.notification-cnt')

        self.assertTrue(notification_count_el)
        self.assertEqual(notification_count_el[0].text_content().strip(), '2')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_THREE_NEWS)
    def test_count_3(self, mock_get):
        notification = self._render_notification()
        notification_count_el = notification.cssselect('.notification-cnt')

        self.assertTrue(notification_count_el)
        self.assertEqual(notification_count_el[0].text_content().strip(), '3')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_THREE_NEWS)
    def test_css_class(self, mock_get):
        notification = self._render_notification()

        important_label = notification.cssselect('.notify-label .label-important')
        self.assertTrue(important_label)
        self.assertEqual(important_label[0].text_content().strip(), 'ERROR')

        warning_label = notification.cssselect('.notify-label .label-warning')
        self.assertTrue(warning_label)
        self.assertEqual(warning_label[0].text_content().strip(), 'RUNNING')

        success_label = notification.cssselect('.notify-label .label-success')
        self.assertTrue(success_label)
        self.assertEqual(success_label[0].text_content().strip(), 'SUCCESS')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_THREE_NEWS)
    def test_parsed_task_name(self, mock_get):
        notification = self._render_notification()

        desc_els = notification.cssselect('.notify-task')

        self.assertEqual(desc_els[0].text_content().strip(), 'task name: task_1')
        self.assertEqual(desc_els[1].text_content().strip(), 'task name: task_2')
        self.assertEqual(desc_els[2].text_content().strip(), 'task name: task_3')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications',
           return_value=THREE_TASKS_THREE_NEWS)
    def test_parsed_database_name(self, mock_get):
        notification = self._render_notification()

        database_els = notification.cssselect('.notify-database')

        self.assertEqual(database_els[0].text_content().strip(), 'database: fake_database_name_1')
        self.assertEqual(database_els[1].text_content().strip(), 'database: fake_database_name_from_obj')
        self.assertEqual(database_els[2].text_content().strip(), 'database: fake_database_name_3')

    @patch('notification.templatetags.notification_tags.UserTasks.get_notifications')
    def test_add_class_new_when_not_read(self, mock_get):
        resp = copy.deepcopy(THREE_TASKS_TWO_NEWS)
        resp[0]['read'] = 1
        mock_get.return_value = resp
        notification = self._render_notification()

        not_read_els = notification.cssselect('li.new')

        self.assertTrue(not_read_els)
