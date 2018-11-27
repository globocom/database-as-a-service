from mock import patch, MagicMock
from workflow.steps.util.host_provider import (Provider,
                                               HostProviderStartVMException,
                                               HostProviderStopVMException)
from physical.tests import factory as physical_factory
from workflow.tests.test_host_provider import BaseCreateVirtualMachineTestCase
from dbaas_credentials.tests import factory as credential_factory
from dbaas_credentials.models import CredentialType
from requests.models import Response


class BaseProviderTestCase(BaseCreateVirtualMachineTestCase):

    def setUp(self):
        super(BaseProviderTestCase, self).setUp()
        self.env = physical_factory.EnvironmentFactory.create(
            name='fake_env'
        )
        self.provider = Provider(self.instance, self.env)
        self.credential = credential_factory.CredentialFactory.create(
            integration_type__name='HOST_PROVIDER',
            integration_type__type=CredentialType.HOST_PROVIDER,
            endpoint='fake_endpoint',
            user='fake_user',
            password='fake_password',
            project='fake_project'
        )
        self.credential.environments.add(self.env)
        self.host = physical_factory.HostFactory.create(
            identifier='fake_identifier1'
        )
        self.instance.hostname = self.host
        self.instance.save()

    @staticmethod
    def _create_fake_response(status_code=200):
        fake_response = Response()
        fake_response.status_code = status_code
        return fake_response


@patch('workflow.steps.util.host_provider.post')
class StartTestCase(BaseProviderTestCase):

    @patch('workflow.steps.util.host_provider.post')
    def test_params(self, post_mock):
        self.provider.start()
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/start'
        )
        expected_json = {
            'host_id': 'fake_identifier1'
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        resp = self.provider.start()

        self.assertTrue(resp)

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderStartVMException):
            self.provider.start()

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderStartVMException):
            self.provider.start()


@patch('workflow.steps.util.host_provider.post')
class StopTestCase(BaseProviderTestCase):

    def test_params(self, post_mock):
        self.provider.stop()
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/stop'
        )
        expected_json = {
            'host_id': 'fake_identifier1'
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        resp = self.provider.stop()
        self.assertTrue(resp)

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderStopVMException):
            self.provider.stop()

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderStopVMException):
            self.provider.stop()
