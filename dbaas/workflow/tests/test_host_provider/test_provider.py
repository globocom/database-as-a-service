from mock import patch, MagicMock
from workflow.steps.util.host_provider import (Provider,
                                               HostProviderStartVMException,
                                               HostProviderStopVMException,
                                               HostProviderNewVersionException,
                                               HostProviderChangeOfferingException,
                                               HostProviderCreateVMException,
                                               HostProviderDestroyVMException,
                                               HostProviderListZoneException,
                                               HostProviderInfoException)
from physical.tests import factory as physical_factory
from workflow.tests.test_host_provider import BaseCreateVirtualMachineTestCase
from dbaas_credentials.tests import factory as credential_factory
from dbaas_credentials.models import CredentialType
from requests.models import Response


__all__ = ('StartTestCase', 'StopTestCase', 'NewVersionTestCase',
           'NewOfferingTestCase', 'CreateHostTestCase', 'DestroyTestCase',
           'ListZonesTestCase', 'HostInfoTestCase')


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
    def _create_fake_response(status_code=200, json=None):
        fake_response = Response()
        fake_response.status_code = status_code
        if json:
            fake_response.json = MagicMock(return_value=json)
        return fake_response


@patch('workflow.steps.util.host_provider.post')
class StartTestCase(BaseProviderTestCase):

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


@patch('workflow.steps.util.host_provider.post')
class NewVersionTestCase(BaseProviderTestCase):

    def test_params_with_engine(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        self.provider.new_version(engine=self.infra.engine)
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/reinstall'
        )
        expected_json = {
            'host_id': 'fake_identifier1',
            'engine': self.infra.engine.full_name_for_host_provider
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_params_without_engine(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        self.provider.new_version()
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/reinstall'
        )
        expected_json = {
            'host_id': 'fake_identifier1',
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        resp = self.provider.new_version(engine=self.infra.engine)
        self.assertTrue(resp)

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderNewVersionException):
            self.provider.new_version(engine=self.infra.engine)

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderNewVersionException):
            self.provider.new_version(engine=self.infra.engine)


@patch('workflow.steps.util.host_provider.post')
class NewOfferingTestCase(BaseProviderTestCase):

    def test_params(self, post_mock):
        self.weaker_offering.cpus = 2
        self.weaker_offering.memory_size_mb = 999
        self.weaker_offering.save()
        post_mock.return_value = self._create_fake_response(status_code=200)
        self.provider.new_offering(offering=self.weaker_offering)
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/resize'
        )
        expected_json = {
            'host_id': 'fake_identifier1',
            'cpus': 2,
            'memory': 999
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        resp = self.provider.new_offering(offering=self.weaker_offering)
        self.assertTrue(resp)

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderChangeOfferingException):
            self.provider.new_offering(offering=self.weaker_offering)

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderChangeOfferingException):
            self.provider.new_offering(offering=self.weaker_offering)


@patch('workflow.steps.util.host_provider.post')
class CreateHostTestCase(BaseProviderTestCase):

    def setUp(self):
        super(CreateHostTestCase, self).setUp()
        self.vm_credential = credential_factory.CredentialFactory.create(
            integration_type__name='VM',
            integration_type__type=CredentialType.VM,
            user='fake_user',
            password='fake_password',
        )
        self.vm_credential.environments.add(self.env)
        self.credential.project = 'fake_provider'
        self.credential.save()
        self.fake_resp = {
            'address': 'fake_address',
            'id': 'fake_id'
        }

    def test_params(self, post_mock):
        self.weaker_offering.cpus = 2
        self.weaker_offering.memory_size_mb = 999
        self.weaker_offering.save()
        post_mock.return_value = self._create_fake_response(
            status_code=201,
            json=self.fake_resp
        )
        self.provider.create_host(
            infra=self.infra,
            offering=self.weaker_offering,
            name='fake_host01',
            team_name='fake_team',
            zone='fake_zone'
        )
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_provider/fake_env/host/new'
        )
        expected_json = {
            'engine': 'fake_unique',
            'name': 'fake_host01',
            'cpu': 2,
            'memory': 999,
            'group': self.infra.name,
            'team_name': 'fake_team',
            'zone': 'fake_zone'
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_201(self, post_mock):
        post_mock.return_value = self._create_fake_response(
            status_code=201,
            json=self.fake_resp
        )
        created_host = self.provider.create_host(
            infra=self.infra,
            offering=self.weaker_offering,
            name='fake_host01',
            team_name='fake_team',
            zone='fake_zone'
        )

        self.assertEqual(created_host.address, 'fake_address')
        self.assertEqual(created_host.hostname, 'fake_address')
        self.assertEqual(created_host.user, 'fake_user')
        self.assertEqual(created_host.password, 'fake_password')
        self.assertEqual(created_host.provider, 'fake_provider')
        self.assertEqual(created_host.identifier, 'fake_id')
        self.assertEqual(created_host.offering.id, self.weaker_offering.id)

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        with self.assertRaises(HostProviderCreateVMException):
            self.provider.create_host(
                infra=self.infra,
                offering=self.weaker_offering,
                name='fake_host01',
                team_name='fake_team',
                zone='fake_zone'
            )

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderCreateVMException):
            self.provider.create_host(
                infra=self.infra,
                offering=self.weaker_offering,
                name='fake_host01',
                team_name='fake_team',
                zone='fake_zone'
            )

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderCreateVMException):
            self.provider.create_host(
                infra=self.infra,
                offering=self.weaker_offering,
                name='fake_host01',
                team_name='fake_team',
                zone='fake_zone'
            )


@patch('workflow.steps.util.host_provider.delete')
class DestroyTestCase(BaseProviderTestCase):

    def setUp(self):
        super(DestroyTestCase, self).setUp()
        self.fake_new_host = MagicMock()
        self.fake_new_host.identifier = 'fake_identifier1'

    def test_params(self, delete_mock):
        self.provider.destroy_host(self.fake_new_host)
        self.assertTrue(delete_mock.called)
        post_params = delete_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/fake_identifier1'
        )
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, delete_mock):
        delete_mock.return_value = self._create_fake_response(status_code=200)
        resp = self.provider.destroy_host(self.fake_new_host)
        self.assertEqual(resp, None)

    def test_404(self, delete_mock):
        delete_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderDestroyVMException):
            self.provider.destroy_host(self.fake_new_host)

    def test_500(self, delete_mock):
        delete_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderDestroyVMException):
            self.provider.destroy_host(self.fake_new_host)


@patch('workflow.steps.util.host_provider.get')
class ListZonesTestCase(BaseProviderTestCase):

    def test_params(self, get_mock):
        get_mock.return_value = self._create_fake_response(
            status_code=200,
            json={'zones': []}
        )
        self.provider.list_zones()
        self.assertTrue(get_mock.called)
        post_params = get_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/zones'
        )
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, get_mock):
        fake_zones = {
            'zones': ['fake_zone1', 'fake_zone2']
        }
        get_mock.return_value = self._create_fake_response(
            status_code=200,
            json=fake_zones
        )
        resp = self.provider.list_zones()

        self.assertListEqual(resp, fake_zones['zones'])

    def test_404(self, get_mock):
        get_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderListZoneException):
            self.provider.list_zones()

    def test_500(self, get_mock):
        get_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderListZoneException):
            self.provider.list_zones()


@patch('workflow.steps.util.host_provider.get')
class HostInfoTestCase(BaseProviderTestCase):
    def setUp(self):
        super(HostInfoTestCase, self).setUp()
        self.fake_new_host = MagicMock()
        self.fake_new_host.identifier = 'fake_identifier1'
        self.fake_resp = {'id': 1, 'name': 'fake_name'}

    def test_params(self, get_mock):
        get_mock.return_value = self._create_fake_response(
            status_code=200,
            json=self.fake_resp
        )
        self.provider.host_info(self.fake_new_host)
        self.assertTrue(get_mock.called)
        post_params = get_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_project/fake_env/host/fake_identifier1'
        )
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_200(self, get_mock):
        get_mock.return_value = self._create_fake_response(
            status_code=200,
            json=self.fake_resp
        )
        resp = self.provider.host_info(self.fake_new_host)

        self.assertDictEqual(resp, self.fake_resp)

    def test_404(self, get_mock):
        get_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(HostProviderInfoException):
            self.provider.host_info(self.fake_new_host)

    def test_500(self, get_mock):
        get_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(HostProviderInfoException):
            self.provider.host_info(self.fake_new_host)
