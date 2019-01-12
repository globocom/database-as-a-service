# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from requests import post, delete, get
from dbaas_credentials.models import CredentialType
from dbaas_dnsapi.utils import get_dns_name_domain, add_dns_record
from physical.models import Vip, Instance, Environment
from util import get_credentials_for
from base import BaseInstanceStep
from vm import WaitingBeReady
from dbaas_dnsapi.models import FOXHA
from workflow.steps.util.base import HostProviderClient


CHANGE_MASTER_ATTEMPS = 4
CHANGE_MASTER_SECONDS = 15


class HostProviderException(Exception):
    pass


class HostProviderCreateVIPException(HostProviderException):
    pass


class HostProviderRegisterVIPException(HostProviderException):
    pass


class HostProviderDestroyVIPException(HostProviderException):
    pass


class HostProviderListZoneException(HostProviderException):
    pass


class HostProviderInfoException(HostProviderException):
    pass


class Provider(object):

    def __init__(self, instance, environment):
        self.instance = instance
        self._credential = None
        self._vm_credential = None
        self._environment = environment

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def plan(self):
        return self.infra.plan

    @property
    def environment(self):
        return self._environment

    @property
    def host(self):
        return self.instance.hostname

    @property
    def engine(self):
        return self.infra.engine.full_name_for_host_provider

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.VIP_PROVIDER
            )

        return self._credential

    @property
    def vm_credential(self):
        if not self._vm_credential:
            self._vm_credential = get_credentials_for(
                self.environment, CredentialType.VM,
            )

        return self._vm_credential

    @property
    def provider(self):
        return self.credential.project

    def _request(self, action, url, **kw):
        auth = (self.credential.user, self.credential.password,)
        kw.update(**{'auth': auth} if self.credential.user else {})
        return action(url, **kw)

    def create_vip(self, infra, port, team_name, equipments,
        vip_dns, database_name=''):
        url = "{}/{}/{}/vip/new".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "group": infra.name,
            "port": port,
            "team_name": team_name,
            "equipments": equipments,
            "vip_dns": vip_dns,
            "database_name": database_name
        }

        response = self._request(post, url, json=data, timeout=600)
        if response.status_code != 201:
            raise HostProviderCreateVIPException(response.content, response)

        content = response.json()

        vip = Vip()
        vip.identifier = content["identifier"]
        vip.infra = infra
        vip.save()
        vip.vip_ip = content["ip"]

        return vip

    def register_instance(self, infra, zone_id, instance_id, port):
        url = "{}/{}/{}/vip/register_target".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "vip_id": Vip.objects.get(infra=infra).identifier,
            "port": port,
            "instance_id": instance_id,
            "zone_id": zone_id
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise HostProviderRegisterVIPException(response.content, response)

    def destroy_vip(self, identifier):
        url = "{}/{}/{}/vip/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            identifier
        )
        response = self._request(delete, url)
        if not response.ok:
            raise HostProviderDestroyVIPException(response.content, response)


class VipProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(VipProviderStep, self).__init__(instance)
        self.driver = self.instance and self.infra.get_driver()
        self.credentials = None
        self._provider = None
        self.host_prov_client = HostProviderClient(self.environment)

    @property
    def provider(self):
        if not self._provider:
            self._provider = Provider(self.instance, self.environment)
        return self._provider

    @property
    def vm_properties(self):
        if not (hasattr(self, '_vm_properties') and self._vm_properties):
            self._vm_properties = self.host_prov_client.get_vm_by_host(
                self.host)
        return self._vm_properties

    @property
    def equipments(self):
        equipments = []
        for instance in self.infra.instances.all():
            host = instance.hostname
            vm_info = self.host_prov_client.get_vm_by_host(host)
            equipment = {
                'host_address': host.address,
                'port': instance.port,
                'identifier': vm_info.identifier
            }
            equipments.append(equipment)
        return equipments

    @property
    def team(self):
        ## TODO
        return "dbaas"
        if self.has_database:
            return self.database.team.name
        return self.create.team.name

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateVip(VipProviderStep):

    def __unicode__(self):
        return "Creating vip..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    @property
    def vip_dns(self):
        name, domain = get_dns_name_domain(self.infra, self.infra.name, FOXHA, is_database=False)
        return '{}.{}'.format(name, domain)

    def do(self):
        if not self.is_valid:
            return

        vip = self.provider.create_vip(
            self.infra, self.instance.port, self.team,
            self.equipments, self.vip_dns)
        dns = add_dns_record(self.infra, self.infra.name, vip.vip_ip, FOXHA, is_database=False)

        self.infra.endpoint = "{}:{}".format(vip.vip_ip, 3306)
        self.infra.endpoint_dns = "{}:{}".format(dns, 3306)
        self.infra.save()

    def undo(self):
        if not self.is_valid:
            return

        try:
            vip = Vip.objects.get(infra=self.infra)
        except ObjectDoesNotExist:
            return
        else:
            self.provider.destroy_vip(vip.identifier)
            vip.delete()


class RegisterInstance(VipProviderStep):

    def __unicode__(self):
        return "Registering instance on vip..."

    @property
    def is_valid(self):
        try:
            self.provider.credential
        except IndexError:
            return False
        else:
            return True

    def do(self):
        if not self.is_valid:
            return
        self.provider.register_instance(
            self.infra,
            self.vm_properties.zone,
            self.vm_properties.identifier,
            self.instance.port
        )

    def undo(self):
        pass
