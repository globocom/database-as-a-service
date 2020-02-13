from mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils.datastructures import MultiValueDictKeyError

from account.models import Role, Team, Organization
from physical.tests.factory import EnvironmentFactory, PlanFactory
from physical.models import Plan


class ValidationTestCase(TestCase):
    """HTTP test cases for the tsuru Service Add. This class focuses on
       validations of POST
    """
    USERNAME = "fake_user"
    PASSWORD = "123456"

    def setUp(self):
        self.role = Role.objects.get_or_create(name="fake_role")[0]
        self.organization = Organization.objects.get_or_create(
            name='fake_organization'
        )[0]
        self.team = Team.objects.get_or_create(
            name="fake_team", role=self.role,
            organization=self.organization)[0]
        self.superuser = User.objects.create_superuser(
            self.USERNAME,
            email="{}@admin.com".format(self.USERNAME),
            password=self.PASSWORD
        )
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.env = 'dev'
        self.environment = EnvironmentFactory.create(name=self.env)
        self.url = reverse('tsuru:service-add', args=(self.env,))
        self.name = 'fake_database'
        self.user = '{}@admin.com'.format(self.USERNAME)
        self.description = 'fake desc'
        self.plan = PlanFactory(name='fake_plan', provider=Plan.CLOUDSTACK)
        self.plan.environments.add(self.environment)
        self.plan_name = 'fake-plan-dev'

    def tearDown(self):
        self.client.logout()

    def _assert_resp(self, resp, msg):
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, msg)

    def test_name_not_in_payload(self):
        with self.assertRaises(MultiValueDictKeyError):
            self.client.post(self.url, {})

    def test_user_not_in_payload(self):
        with self.assertRaises(MultiValueDictKeyError):
            self.client.post(
                self.url,
                {'name': self.name}
            )

    def test_team_not_in_payload(self):
        with self.assertRaises(MultiValueDictKeyError):
            self.client.post(
                self.url,
                {'name': self.name, 'user': self.user}
            )

    def test_description_fail(self):
        resp = self.client.post(
            self.url,
            {'name': self.name, 'user': self.user, 'team': self.team}
        )
        self._assert_resp(resp, '"A description must be provided."')

    def test_name_fail(self):
        resp = self.client.post(
            self.url,
            {
                'name': '99invalid-name',
                'user': self.user,
                'description': self.description,
                'team': self.team
            }
        )
        self._assert_resp(
            resp,
            '"Your database name must match /^[a-z][a-z0-9_]+$/ ."'
        )

    @patch(
        'tsuru.views.TaskHistory.objects.filter',
    )
    @patch('tsuru.views.Database.objects.get', new=MagicMock())
    def test_database_found(self, mock_filter):
        mock_filter().last.return_value = []
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team
            }
        )
        self._assert_resp(
            resp,
            '"There is already a database called fake_database in dev."'
        )

    @patch('tsuru.views.TaskHistory.objects.filter', new=MagicMock())
    @patch('tsuru.views.Database.objects.get', new=MagicMock())
    def test_database_being_deleted(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team
            }
        )
        self._assert_resp(
            resp,
            '"There is a database called fake_database being deleted."'
        )

    @patch(
        'tsuru.views.database_name_evironment_constraint',
        new=MagicMock(return_value=True)
    )
    def test_already_exist_database_with_name(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team
            }
        )
        self._assert_resp(
            resp,
            '"fake_database already exists in env dev!"'
        )

    def test_user_not_found(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': 'another_user@not_found.com',
                'description': self.description,
                'team': self.team
            }
        )
        self._assert_resp(
            resp,
            '"User does not exist."'
        )

    def test_team_not_found(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': 'team_not_found'
            }
        )
        self._assert_resp(
            resp,
            '"Team does not exist."'
        )

    def test_env_not_found(self):
        self.url = self.url.replace(
            '/{}/'.format(self.env),
            '/env_not_found/'
        )
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team.name
            }
        )
        self._assert_resp(
            resp,
            '"Environment does not exist."'
        )

    @patch(
        'tsuru.views.Team.count_databases_in_use',
        new=MagicMock(return_value=99)
    )
    def test_allocation_limit(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team.name
            }
        )
        self._assert_resp(
            resp,
            ('"The database alocation limit of 2 has been exceeded for the '
             'selected team: fake_team"')
        )

    def test_plan_not_on_payload(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team.name
            }
        )
        self._assert_resp(
            resp,
            '"Plan was not found"'
        )

    def test_plan_not_found(self):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team.name,
                'plan': 'not found'
            }
        )
        self._assert_resp(
            resp,
            '"Plan was not found"'
        )

    @patch('notification.tasks.TaskRegister.create_task', new=MagicMock())
    @patch('notification.tasks.create_database_with_retry')
    def test_call_database_create(self, create_database_mock):
        resp = self.client.post(
            self.url,
            {
                'name': self.name,
                'user': self.user,
                'description': self.description,
                'team': self.team.name,
                'plan': self.plan_name
            }
        )

        self.assertTrue(create_database_mock.called)
        self.assertEqual(resp.status_code, 201)
