import socket
from time import sleep
from requests import post, get
from physical.models import Vip
from base import BaseInstanceStep
from util import get_credentials_for
from dbaas_dnsapi.models import FOXHA
from dbaas_dnsapi.utils import add_dns_record
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_credentials.models import CredentialType


class IngressProvider(object):

    def __init__(self, instance):
        self.instance = instance
        self._team = None
        self._credential = None
        self._ip = None
        self._port = None

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def host(self):
        return self.instance.hostname

    @property
    def team(self):
        return self.infra.databases.first().team.name

    @property
    def port(self):
        return int(self.instance.port)

    @property
    def is_database(self):
        return self.instance.is_database

    def _request(self, action, url, **kw):
        return action(url, verify=False, **kw)

    @property
    def ip(self):
        return self._ip

    def credential(self):
        print('*-----------------------INSERTING CREDENTIAL----------------------------*')
        print(f'*-----------------------ENVIRONMENT [{self.infra.environment}]----------------------------*')
        if not self._credential:
            self._credential = get_credentials_for(
                self.infra.environment, CredentialType.INGRESS_PROVIDER
            )
        print('*-----------------------CREATED CREDENTIAL----------------------------*')
        print(f'*-----------------------[{self._credential}]----------------------------*')
        return self._credential

    def create_ingress(self, infra, port, team_name):
        data = {
            "team": team_name,
            "bank_port": port,
            "bank_address": [str(infra.hosts[0].address)],
            "bank_type": 'MySQLFOXHA',
            "bank_name": infra.name_prefix,
            "bank_service_account": str(infra.service_account)
        }
        try:
            response = self._request(post, self.credential.endpoint, json=data, timeout=6000)

            if response.status_code not in [200, 201]:
                raise response.raise_for_status()
            ingress = response.json()['value']

        except Exception as error:
            print(error)
            raise Exception
        self._port = ingress['port_external']
        self._team = team_name
        return ingress


class IngressProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(IngressProviderStep, self).__init__(instance)
        self._ingress_provider = None

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    @property
    def vip_ip(self):
        return self.ingressprovider.ip

    @property
    def ingressprovider(self):
        if not self._ingress_provider:
            self._ingress_provider = IngressProvider(self.instance)
        return self._ingress_provider

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class AllocateProvider(IngressProviderStep):

    def __unicode__(self):
        return "Allocating Provider on k8s cluster..."

    def update_infra_endpoint(self, ip, port):
        self.infra.endpoint = "{}:{}".format(ip, port)
        self.infra.save()

    def generate_new_vip(self):
        ingress = self.ingressprovider.create_ingress(
            self.infra,
            self.ingressprovider.port,
            self.team_name)
        return ingress

    def register_ingress_vip(self, ingress):
        print('*-----------------------------------*INGRESS*-----------------------------------*')
        print(ingress)
        try:
            original_vip = Vip.objects.get(infra=self.infra)
        except Vip.DoesNotExist:
            original_vip = None
        vip = Vip()
        vip.identifier = ingress['port_external']
        vip.infra = self.infra
        vip.vip_ip = ingress['ip_external']
        if original_vip:
            vip.original_vip = original_vip
        vip.save()
        print('*-----------------------////////----------------------------*')
        return vip

    def insert_dns_on_infra(self, ingress):
        if self._vip.vip_ip == ingress['ip_external']:
            print('*-----------------------INSERTING DNS----------------------------*')
            dns = add_dns_record(
                databaseinfra=self.infra,
                name=self.infra.name,
                ip=ingress['ip_external'],
                type=FOXHA,
                is_database=False
            )
            if dns is None:
                return
        self.infra.endpoint_dns = "{}:{}".format(dns, ingress['port_external'])
        self.infra.save()

    def do(self):
        if not self.is_valid:
            return
        ingress = self.generate_new_vip()
        self.update_infra_endpoint(ingress['ip_external'], ingress['port_external'])
        self._vip = self.register_ingress_vip(ingress)
        self.insert_dns_on_infra(ingress)
        return True

    def undo(self):
        pass


class RegisterDNSIngress(IngressProviderStep):

    def __init__(self, *args, **kw):
        super(RegisterDNSIngress, self).__init__(*args, **kw)
        self.provider = DNSAPIProvider
        self.do_export = True

    def __unicode__(self):
        return "Registry dns for VIP..."

    @staticmethod
    def is_ipv4(ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def _do_database_dns_for_ip(self, func):
        if not self.is_valid:
            return
        try:
            ip = self.ingressprovider.ip
            if ip is None:
                ip = self.instance.address
        except Exception as error:
            pass
        return func(
            databaseinfra=self.ingressprovider.infra,
            ip=ip,
            do_export=self.do_export,
            env=self.ingressprovider.infra.environment,
            **{'dns_type': 'CNAME'} if not self.is_ipv4(ip) else {}
        )

    def do(self):
        if not self.is_valid:
            return
        self._do_database_dns_for_ip(self.provider.create_database_dns_for_ip)

    def undo(self):
        self._do_database_dns_for_ip(self.provider.remove_databases_dns_for_ip)
