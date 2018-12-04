from django.core.exceptions import ObjectDoesNotExist
from dbaas_dnsapi.utils import get_dns_name_domain, add_dns_record
from dbaas_dnsapi.models import FOXHA
from dbaas_networkapi.dbaas_api import DatabaseAsAServiceApi
from dbaas_networkapi.equipment import Equipment
from dbaas_networkapi.provider import NetworkProvider
from dbaas_networkapi.utils import get_vip_ip_from_databaseinfra
from base import BaseInstanceStep
from workflow.steps.util.base import HostProviderClient



class Network(BaseInstanceStep):

    def __init__(self, instance):
        super(Network, self).__init__(instance)
        self.api = DatabaseAsAServiceApi(self.infra)
        self.provider = NetworkProvider(self.api)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class CreateVip(Network):

    def __unicode__(self):
        return "Creating VIP..."

    @property
    def equipments(self):
        equipments = []
        host_provider_cli = HostProviderClient(self.infra.environment)
        for instance in self.infra.instances.all():
            host = instance.hostname
            vm = host_provider_cli.get_vm_by_host(host)
            if vm is None:
                raise Exception(
                    "Cannot get information for host {} for identifier {}".format(
                        host,
                        host.identifier
                    )
                )
            equipment = Equipment(
                '{}-{}'.format(self.api.vm_name, vm.identifier),
                host.address, instance.port
            )
            equipments.append(equipment)

        return equipments

    @property
    def vip_dns(self):
        name, domain = get_dns_name_domain(self.infra, self.infra.name, FOXHA, is_database=False)
        return '{}.{}'.format(name, domain)

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return

        vip = self.provider.create_vip(self.equipments, 3306, self.vip_dns)
        dns = add_dns_record(self.infra, self.infra.name, vip.vip_ip, FOXHA, is_database=False)

        self.infra.endpoint = "{}:{}".format(vip.vip_ip, 3306)
        self.infra.endpoint_dns = "{}:{}".format(dns, 3306)
        self.infra.save()

    def undo(self):
        try:
            vip_ip = get_vip_ip_from_databaseinfra(self.infra)
        except ObjectDoesNotExist:
            return
        else:
            self.provider.delete_vip(vip_ip)
