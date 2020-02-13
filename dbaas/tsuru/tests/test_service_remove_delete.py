from mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from rest_framework import status

from account.models import Role, Team, Organization


@patch('tsuru.views.TaskRegister')
@patch('tsuru.views.get_database')
class ServiceRemoveDeleteTestCase(TestCase):
    USERNAME = "test-ui-database"
    PASSWORD = "123456"

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.organization = Organization.objects.get_or_create(
            name='fake_organization'
        )[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role,
            organization=self.organization
        )[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME,
            email="%s@admin.com" % self.USERNAME,
            password=self.PASSWORD
        )
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tearDown(self):
        self.client.logout()

    def test_database_not_found(self, mock_get_database, mock_task_register):
        mock_get_database.side_effect = IndexError
        url = reverse('tsuru:service-remove', args=('dev', 'test_database'))
        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_database_delete(self, mock_get_database, mock_task_register):
        url = reverse('tsuru:service-remove', args=('dev', 'test_database'))
        response = self.client.delete(url)

        self.assertTrue(mock_get_database().delete.called)
        self.assertFalse(mock_task_register.database_destroy.called)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_need_purge(self, mock_get_database, mock_task_register):
        url = reverse('tsuru:service-remove', args=('dev', 'test_database'))
        url = "{}{}".format(url, "?purge=1")
        response = self.client.delete(url)

        self.assertTrue(mock_task_register.database_destroy.called)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_dont_purge(self, mock_get_database, mock_task_register):
        url = reverse('tsuru:service-remove', args=('dev', 'test_database'))
        url = "{}{}".format(url, "?purge=0")
        response = self.client.delete(url)

        self.assertFalse(mock_task_register.database_destroy.called)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
