from mock import patch, MagicMock
from workflow.steps.util.vip_provider import (Provider,
                                              VipProviderCreateVIPException,
                                              VipProviderUpdateVipRealsException,
                                              VipProviderAddVIPRealException,
                                              VipProviderRemoveVIPRealException,
                                              VipProviderWaitVIPReadyException,
                                              VipProviderDestroyVIPException,
                                              VipProviderListZoneException,
                                              VipProviderInfoException)
from physical.tests import factory as physical_factory
from workflow.tests.test_host_provider import BaseCreateVirtualMachineTestCase
from dbaas_credentials.tests import factory as credential_factory
from dbaas_credentials.models import CredentialType
from requests.models import Response
from collections import namedtuple


__all__ = ('CreateVipTestCase',)


class BaseProviderTestCase(BaseCreateVirtualMachineTestCase):

    def setUp(self):
        super(BaseProviderTestCase, self).setUp()
        self.env = physical_factory.EnvironmentFactory.create(
            name='fake_env'
        )
        self.provider = Provider(self.instance, self.env)
        self.credential = credential_factory.CredentialFactory.create(
            integration_type__name='VIP_PROVIDER',
            integration_type__type=CredentialType.VIP_PROVIDER,
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


@patch('workflow.steps.util.vip_provider.post')
class CreateVipTestCase(BaseProviderTestCase):

    def setUp(self):
        super(CreateVipTestCase, self).setUp()
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
            'identifier': 'fake_vip_identifier',
            'ip': 'fake_vip_ip'
        }

    # @patch('workflow.steps.util.vip_provider.HostProviderClient.get_vm_by_host',
    #        return_value=namedtuple('VMPropertiesFake', 'identifier')('fake_identifier'))
    def test_params(self, post_mock):
        post_mock.return_value = self._create_fake_response(
            status_code=201,
            json=self.fake_resp
        )
        self.provider.create_vip(
            infra=self.infra,
            port=999,
            team_name='fake_team',
            equipments={
                'host_address': self.host.address,
                'port': self.instance.port,
                'identifier': 'fake_identifier'
            },
            vip_dns='fake_vip_dns',
            database_name=''
        )
        self.assertTrue(post_mock.called)
        post_params = post_mock.call_args
        self.assertEqual(
            post_params[0][0],
            'fake_endpoint/fake_provider/fake_env/vip/new'
        )
        expected_json = {
            'port': 999,
            'equipments': {
                'host_address': self.host.address,
                'port': self.instance.port,
                'identifier': 'fake_identifier'
            },
            'group': self.infra.name,
            'team_name': 'fake_team',
            'vip_dns': 'fake_vip_dns',
            'database_name': ''
        }
        self.assertDictEqual(post_params[1]['json'], expected_json)
        self.assertEqual(post_params[1]['auth'], ('fake_user', 'fake_password'))

    def test_201(self, post_mock):
        post_mock.return_value = self._create_fake_response(
            status_code=201,
            json=self.fake_resp
        )
        created_vip = self.provider.create_vip(
            infra=self.infra,
            port=999,
            team_name='fake_team',
            equipments={
                'host_address': self.host.address,
                'port': self.instance.port,
                'identifier': 'fake_identifier'
            },
            vip_dns='fake_vip_dns',
            database_name=''
        )

        self.assertEqual(created_vip.infra.id, self.infra.id)
        self.assertEqual(created_vip.vip_ip, 'fake_vip_ip')
        self.assertEqual(created_vip.identifier, 'fake_vip_identifier')

    def test_200(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=200)
        with self.assertRaises(VipProviderCreateVIPException):
            self.provider.create_vip(
                infra=self.infra,
                port=999,
                team_name='fake_team',
                equipments={
                    'host_address': self.host.address,
                    'port': self.instance.port,
                    'identifier': 'fake_identifier'
                },
                vip_dns='fake_vip_dns',
                database_name=''
            )

    def test_404(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=404)
        with self.assertRaises(VipProviderCreateVIPException):
            self.provider.create_vip(
                infra=self.infra,
                port=999,
                team_name='fake_team',
                equipments={
                    'host_address': self.host.address,
                    'port': self.instance.port,
                    'identifier': 'fake_identifier'
                },
                vip_dns='fake_vip_dns',
                database_name=''
            )

    def test_500(self, post_mock):
        post_mock.return_value = self._create_fake_response(status_code=500)
        with self.assertRaises(VipProviderCreateVIPException):
            self.provider.create_vip(
                infra=self.infra,
                port=999,
                team_name='fake_team',
                equipments={
                    'host_address': self.host.address,
                    'port': self.instance.port,
                    'identifier': 'fake_identifier'
                },
                vip_dns='fake_vip_dns',
                database_name=''
            )
