from mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse

from physical.models import Plan, Environment
from system.models import Configuration
from model_mommy import mommy
from slugify import slugify

import json


class BaseListPlansTestCase(TestCase):
    USERNAME = "fake_user"
    PASSWORD = "123456"
    plan_name = 'fake-plan-dev'
    env_name = 'dev'
    append_env_url = ""
    valid_environment = True

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
        self.env = self.env_name
        self.environment = mommy.make('Environment',
                                      name=self.env,
                                      provisioner=Environment.CLOUDSTACK,
                                      stage=Environment.DEV,
                                      tsuru_deploy=self.valid_environment)

        self.url = reverse(
            'tsuru:list-plans',
            args=("%s%s" % (self.env, self.append_env_url),))
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

    def tearDown(self):
        self.client.logout()

    def do_request(self):
        return self.client.get(
                    self.url,
                )

    def _assert_resp(self, resp, msg):
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, '"[DBaaS Error] {}"'.format(msg))


class ValidEnvironmentTestCase(BaseListPlansTestCase):

    def test_list_plans(self):
        resp = self.do_request()
        content = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            content[0]["name"],
            "%s-%s" % (self.plan_name, self.env))


class InalidTsuruEnvironmentTestCase(BaseListPlansTestCase):
    valid_environment = False
    env_name = "dev2"

    def test_non_tsuru_deployable_environment(self):
        resp = self.do_request()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, "[]")


class InalidEnvironmentTestCase(BaseListPlansTestCase):
    append_env_url = "X"

    def test_invalid_environment(self):
        resp = self.do_request()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.content, '"Invalid environment"')
