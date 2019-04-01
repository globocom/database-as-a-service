# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from requests import post, delete, put
from dbaas_credentials.models import CredentialType
from dbaas_dnsapi.utils import get_dns_name_domain, add_dns_record
from physical.models import Vip
from util import get_credentials_for
from base import BaseInstanceStep
from dbaas_dnsapi.models import FOXHA
from workflow.steps.util.base import HostProviderClient


CHANGE_MASTER_ATTEMPS = 4
CHANGE_MASTER_SECONDS = 15


class VipProviderException(Exception):
    pass


class VipProviderCreateVIPException(VipProviderException):
    pass


class VipProviderUpdateVipRealsException(VipProviderException):
    pass


class VipProviderAddVIPRealException(VipProviderException):
    pass


class VipProviderRemoveVIPRealException(VipProviderException):
    pass


class VipProviderWaitVIPReadyException(VipProviderException):
    pass


class VipProviderDestroyVIPException(VipProviderException):
    pass


class VipProviderListZoneException(VipProviderException):
    pass


class VipProviderInfoException(VipProviderException):
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
        vip_dns, database_name='', future_vip=False):
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
            raise VipProviderCreateVIPException(response.content, response)

        content = response.json()

        try:
            original_vip = Vip.objects.get(infra=infra)
        except Vip.DoesNotExist:
            original_vip = None
        vip = Vip()
        vip.identifier = content["identifier"]
        vip.infra = infra
        if original_vip:
            vip.original_vip = original_vip
        vip.save()
        vip.vip_ip = content["ip"]

        return vip

    def update_vip_reals(self, vip_reals, vip_identifier):
        url = "{}/{}/{}/vip/{}/reals".format(
            self.credential.endpoint,
            self.provider,
            self.environment,
            vip_identifier
        )
        data = {
            "vip_reals": vip_reals,
        }

        response = self._request(put, url, json=data, timeout=600)
        if not response.ok:
            raise VipProviderUpdateVipRealsException(response.content, response)

    def add_real(self, infra, real_id, port):
        vip_id = Vip.objects.get(infra=infra).identifier
        url = "{}/{}/{}/vip/{}/reals".format(
            self.credential.endpoint, self.provider, self.environment, vip_id
        )
        data = {
            "port": port,
            "real_id": real_id,
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise VipProviderAddVIPRealException(response.content, response)

    def remove_real(self, infra, real_id, port):
        vip_id = Vip.objects.get(infra=infra).identifier
        url = "{}/{}/{}/vip/{}/reals/{}".format(
            self.credential.endpoint, self.provider, self.environment, vip_id,
            real_id
        )

        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise VipProviderRemoveVIPRealException(response.content, response)

    def wait_vip_ready(self, infra):
        url = "{}/{}/{}/vip/healthy".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "vip_id": Vip.objects.get(infra=infra).identifier,
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise VipProviderWaitVIPReadyException(response.content, response)

        response = response.json()
        return response['healthy']


    def destroy_vip(self, identifier):
        url = "{}/{}/{}/vip/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            identifier
        )
        response = self._request(delete, url)
        if not response.ok:
            raise VipProviderDestroyVIPException(response.content, response)


class VipProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(VipProviderStep, self).__init__(instance)
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
            if host.future_host:
                host = host.future_host
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


class CreateVipMigrate(CreateVip):

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return
        self.provider.create_vip(
            self.infra, self.instance.port, self.team,
            self.equipments, self.vip_dns)


class DestroyVipMigrate(CreateVipMigrate):

    def __unicode__(self):
        return "Destroying old vip..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        if not self.is_valid:
            return
        vip = Vip.objects.get(infra=self.infra)
        future_vip = Vip.original_objects.get(
            infra=self.infra, original_vip=vip
        )
        self.provider.destroy_vip(vip.identifier)
        future_vip.original_vip = None
        future_vip.save()
        vip.delete()

    def undo(self):
        return super(DestroyVipMigrate).do()


class UpdateVipReals(VipProviderStep):
    def __unicode__(self):
        return "Update vip reals..."

    @property
    def equipments(self):
        equipments = []
        for instance in self.infra.instances.all():
            host = instance.hostname
            if self.host_migrate and host.future_host and self.rollback is False:
                host = host.future_host
            vm_info = self.host_prov_client.get_vm_by_host(host)
            equipment = {
                'host_address': host.address,
                'port': instance.port,
                'identifier': vm_info.identifier
            }
            equipments.append(equipment)
        return equipments

    @property
    def vip(self):
        original_vip =  Vip.objects.get(infra=self.infra)
        try:
            future_vip = Vip.original_objects.get(
                infra_id=self.infra.id,
                original_vip=original_vip
            )
        except Vip.DoesNotExist:
            return original_vip
        else:
            return future_vip

    def update_vip_reals(self):
        self.provider.update_vip_reals(
            self.equipments,
            vip_identifier=self.vip.identifier,
        )

    def do(self):
        self.rollback = False
        self.update_vip_reals()

    def undo(self):
        self.rollback = True
        self.update_vip_reals()



class UpdateVipRealsMigrate(UpdateVipReals):
    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return
        return super(UpdateVipRealsMigrate, self).do()

    def undo(self):
        if not self.is_valid:
            return
        return super(UpdateVipRealsMigrate, self).undo()


class AddReal(VipProviderStep):

    def __unicode__(self):
        return "Registering real on vip..."

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
        self.provider.add_real(
            self.infra,
            self.vm_properties.identifier,
            self.instance.port
        )

    def undo(self):
        pass


class RemoveReal(VipProviderStep):

    def __unicode__(self):
        return "Removing real from vip..."

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
        self.provider.remove_real(
            self.infra,
            self.vm_properties.identifier,
            self.instance.port
        )

    def undo(self):
        pass

class RemoveRealMigrate(RemoveReal):

    def __unicode__(self):
        return "Removing old real from vip..."

    @property
    def host(self):
        return self.host_migrate.host


class WaitVipReady(VipProviderStep):

    def __unicode__(self):
        return "Waiting vip ready..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return
        vip_ready = self.provider.wait_vip_ready(
            self.infra
        )
        if not vip_ready:
            raise EnvironmentError("VIP not ready")


    def undo(self):
        pass
