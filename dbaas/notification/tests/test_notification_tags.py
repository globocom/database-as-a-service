from mock import patch
from lxml import html as lhtml
from unittest import TestCase
from django.template import Template, Context
from .fakes.get_notifications import (THREE_TASKS_TWO_NEWS, THREE_TASKS_ZERO_NEWS,
                                      THREE_TASKS_THREE_NEWS)


class NotificationCountTestCase(TestCase):
    def setUp(self):
        html = '{% load notification_tags %}'
        html += '{% get_notifications user %}'
        self.notification = Template(html)

    def _render_notification(self):
        return lhtml.fromstring(self.notification.render(Context({'user': 'admin'})))

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

        self.assertTrue(notification.cssselect('.notify-label .label-important'))
        self.assertTrue(notification.cssselect('.notify-label .label-warning'))
        self.assertTrue(notification.cssselect('.notify-label .label-success'))
