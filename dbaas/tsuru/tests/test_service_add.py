from mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse

from physical.models import Plan, Environment
from system.models import Configuration
from model_mommy import mommy
from slugify import slugify


class BaseValidationTestCase(TestCase):
    USERNAME = "fake_user"
    PASSWORD = "123456"
    plan_name = 'fake-plan-dev'
    is_k8s = False
    tsuru_deployable = True

    def setUp(self):
        self.role = mommy.make('Role', name='fake_role')
        self.organization = mommy.make(
            'Organization', name='fake_organization'
        )
        self.team = mommy.make(
            'Team',
            name="fake_team", role=self.role,
            organization=self.organization)
        self.superuser = User.objects.create_superuser(
            self.USERNAME,
            email="{}@admin.com".format(self.USERNAME),
            password=self.PASSWORD
        )
        self.team.users.add(self.superuser)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.env = 'dev'
        self.k8s_env_name = 'k8s_env'
        self.environment = mommy.make('Environment',
                                      name=self.env,
                                      provisioner=Environment.CLOUDSTACK,
                                      stage=Environment.DEV,
                                      tsuru_deploy=self.tsuru_deployable)
        self.k8s_env = mommy.make(
            'Environment',
            name=self.k8s_env_name,
            provisioner=Environment.KUBERNETES,
            stage=Environment.DEV,
            tsuru_deploy=True
        )
        self.url = reverse('tsuru:service-add', args=(self.env,))
        self.name = 'fake_database'
        self.user = '{}@admin.com'.format(self.USERNAME)
        self.description = 'fake desc'
        self.plan = mommy.make(
            'Plan',
            name=self.plan_name,
            provider=Plan.CLOUDSTACK,
            is_active=True
        )
        self.plan.environments.add(self.environment)
        self.payload = {
            'name': self.name,
            'user': self.user,
            'description': self.description,
            'team': self.team.name,
            'plan': slugify("%s-%s" % (
                self.plan_name,
                self.env if not self.is_k8s else self.k8s_env_name
            ))
        }
        self.headers = {
            'HTTP_X_TSURU_POOL_NAME': 'Fake Pool',
            'HTTP_X_TSURU_POOL_PROVISIONER': 'docker'
        }

    def tearDown(self):
        self.client.logout()

    def do_request(self):
        return self.client.post(
                self.url,
                self.payload,
                **self.headers
            )

    def _assert_resp(self, resp, msg):
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, '"[DBaaS Error] {}"'.format(msg))

    def do_request_and_assert(self, msg):
        resp = self.do_request()
        self._assert_resp(resp, msg)


class ValidationRequiredParamsTestCase(BaseValidationTestCase):
    """HTTP test cases for the tsuru Service Add. This class focuses on
       validations required params of POST
    """

    def test_name(self):
        self.payload.pop('name')
        self.do_request_and_assert('Param name must be provided.')

    def test_user(self):
        self.payload.pop('user')
        self.do_request_and_assert('Param user must be provided.')

    def test_team(self):
        self.payload.pop('team')
        self.do_request_and_assert('Param team must be provided.')

    def test_description(self):
        self.payload.pop('description')
        self.do_request_and_assert('Param description must be provided.')

    def test_plan(self):
        self.payload.pop('plan')
        self.do_request_and_assert('Param plan must be provided.')


class NotFoundMetadataValidationTestCase(BaseValidationTestCase):
    """HTTP test cases for the tsuru Service Add. This class focuses on
       validations of POST
    """

    def test_user(self):
        self.payload['user'] = 'another_user@not_found.com'
        self.do_request_and_assert(
            'User <{}> was not found'.format(self.payload['user'])
        )

    def test_team(self):
        self.payload['team'] = 'team_not_found'
        self.do_request_and_assert('Team <{}> was not found'.format(
            self.payload['team'])
        )

    def test_env(self):
        self.url = self.url.replace(
            '/{}/'.format(self.env),
            '/env_not_found/'
        )
        self.do_request_and_assert('Environment was not found')

    def test_plan(self):
        self.payload['plan'] = 'not found'
        self.do_request_and_assert(
            'Plan <{}> was not found'.format(self.payload['plan'])
        )


class OthersValidatetionsTestCase(BaseValidationTestCase):
    @patch('tsuru.views.serviceAdd.Database.objects.get', new=MagicMock())
    def test_database_already_exists(self):
        self.do_request_and_assert(('There is already a database called '
                                    'fake_database in dev.'))

    def test_invalid_database_name(self):
        self.payload['name'] = '99invalid-name'
        self.do_request_and_assert(
            'Your database name must match /^[a-z][a-z0-9_]+$/ .'
        )

    @patch(
        'tsuru.views.serviceAdd.database_name_evironment_constraint',
        new=MagicMock(return_value=True)
    )
    def test_already_exist_database_with_name(self):
        self.do_request_and_assert('fake_database already exists in env dev!')

    @patch(
        'tsuru.views.serviceAdd.Team.count_databases_in_use',
        new=MagicMock(return_value=99)
    )
    def test_allocation_limit(self):
        self.do_request_and_assert(
            ('The database alocation limit of 2 has been exceeded for the '
             'selected team: fake_team')
        )

    @patch('notification.tasks.TaskRegister.create_task', new=MagicMock())
    @patch('notification.tasks.TaskRegister.database_create')
    def test_call_database_create(self, create_database_mock):
        resp = self.do_request()

        self.assertTrue(create_database_mock.called)
        self.assertEqual(resp.status_code, 201)


class GCPValidationTestCase(BaseValidationTestCase):

    tsuru_deployable = False

    def test_create_database_in_non_tsuru_deployable_env(self):
        resp = self.do_request()

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.content,
            '"[DBaaS Error] Plan <%s-%s> was not found"' %
            (self.plan_name, self.env))


class K8sValidationTestCase(BaseValidationTestCase):
    plan_name = 'fake-plan-k8s-env'
    is_k8s = True

    def setUp(self):
        super(K8sValidationTestCase, self).setUp()
        self.plan.environments.remove(self.environment)
        self.plan.environments.add(self.k8s_env)
        self.url = self.url.replace(
            '/{}/'.format(self.env),
            '/{}/'.format(self.k8s_env_name)
        )
        Configuration.objects.create(
            name="k8s_envs", value=self.k8s_env_name
        )
        self.pool_name = 'fake_pool'
        self.pool_endpoint = 'https://www.fake.rancher/endpoint'
        self.pool = mommy.make(
            'Pool',
            name=self.pool_name,
            cluster_endpoint=self.pool_endpoint,
            rancher_token='',
            dbaas_token=''
        )
        self.pool.teams.add(self.team)
        # self.payload['parameters.pool'] = self.pool_name
        self.headers = {
            'HTTP_X_TSURU_POOL_NAME': self.pool_name,
            'HTTP_X_TSURU_POOL_PROVISIONER': 'kubernetes',
            'HTTP_X_TSURU_CLUSTER_NAME': 'fake cluster name',
            'HTTP_X_TSURU_CLUSTER_PROVISIONER': 'rancher',
            'HTTP_X_TSURU_CLUSTER_ADDRESSES': self.pool_endpoint
        }

    def test_pool_not_in_header(self):
        self.headers.pop('HTTP_X_TSURU_POOL_NAME')
        self.do_request_and_assert(
            ("the header <HTTP_X_TSURU_POOL_NAME> was not found "
             "on headers. Contact tsuru team.")
        )

    def test_pool_endpoint_not_in_header(self):
        self.headers.pop('HTTP_X_TSURU_CLUSTER_ADDRESSES')
        self.do_request_and_assert(
            ("the header <HTTP_X_TSURU_CLUSTER_ADDRESSES> was not found "
             "on headers. Contact tsuru team.")
        )

    def test_pool_header_empty(self):
        self.headers['HTTP_X_TSURU_POOL_NAME'] = ''
        self.do_request_and_assert(
            ("the header <HTTP_X_TSURU_POOL_NAME> was not found "
             "on headers. Contact tsuru team.")
        )

    def test_pool_endoint_header_empty(self):
        self.headers['HTTP_X_TSURU_CLUSTER_ADDRESSES'] = ''
        self.do_request_and_assert(
            ("the header <HTTP_X_TSURU_CLUSTER_ADDRESSES> was not found "
             "on headers. Contact tsuru team.")
        )

    def test_pool_not_found(self):
        self.headers['HTTP_X_TSURU_CLUSTER_ADDRESSES'] = (
            'unexistent pool address'
        )
        self.do_request_and_assert(
            "Pool with name <{}> and endpoint <{}> was not found".format(
                self.pool_name,
                self.headers['HTTP_X_TSURU_CLUSTER_ADDRESSES']
            )
        )

    def test_pool_not_on_team_of_user(self):
        self.pool.teams.remove(self.team)
        self.do_request_and_assert(
            "The Team <{}> arent on Pool <{}>".format(
                self.team.name, self.pool_name
            )
        )
