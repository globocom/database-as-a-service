from dbaas_credentials.models import CredentialType
from dbaas_dnsapi.models import HOST, INSTANCE, DatabaseInfraDNSList
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.utils import add_dns_record
from util import get_credentials_for, check_nslookup
from base import BaseInstanceStep
from dbaas_networkapi.models import Vip


class DNSStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DNSStep, self).__init__(instance)
        self.provider = DNSAPIProvider

    @property
    def credentials(self):
        return get_credentials_for(self.environment, CredentialType.DNSAPI)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class ChangeTTL(DNSStep):

    def __unicode__(self):
        return "Changing DNS TLL to {} minutes...".format(self.minutes)

    @property
    def minutes(self):
        raise NotImplementedError

    @property
    def seconds(self):
        return self.minutes * 60

    def do(self):
        self.provider.update_database_dns_ttl(
            self.infra, self.seconds
        )


class ChangeTTLTo5Minutes(ChangeTTL):
    minutes = 5


class ChangeTTLTo3Hours(ChangeTTL):
    minutes = 180


class ChangeEndpoint(DNSStep):

    @property
    def instances(self):
        return self.host_migrate.host.instances.all()

    def __unicode__(self):
        return "Changing DNS endpoint..."

    def update_host_dns(self, origin_host, destiny_host):
        for instance in self.instances:
            DNSAPIProvider.update_database_dns_content(
                self.infra, instance.dns,
                origin_host.address, destiny_host.address
            )

        DNSAPIProvider.update_database_dns_content(
            self.infra, origin_host.hostname,
            origin_host.address, destiny_host.address
        )

        destiny_host.hostname = origin_host.hostname
        origin_host.hostname = origin_host.address
        origin_host.save()
        destiny_host.save()

        if self.infra.endpoint and origin_host.address in self.infra.endpoint:
            self.infra.endpoint = self.infra.endpoint.replace(
                origin_host.address, destiny_host.address
            )
            self.infra.save()


    def do(self):
        self.update_host_dns(self.host_migrate.host, self.host)

    def undo(self):
        self.update_host_dns(self.host, self.host_migrate.host)
        CheckIsReady(self.instance).do()


class CreateDNS(DNSStep):

    def __unicode__(self):
        return "Creating DNS..."

    @property
    def database_sufix(self):
        return {}

    def do(self):
        if self.host.hostname == self.host.address:
            self.host.hostname = add_dns_record(
                databaseinfra=self.infra,
                name=self.instance.vm_name,
                ip=self.host.address,
                type=HOST
            )
            self.host.save()

        self.instance.dns = add_dns_record(
            databaseinfra=self.infra,
            name=self.instance.vm_name,
            ip=self.instance.address,
            type=INSTANCE,
            **self.database_sufix
        )

        self.provider.create_database_dns_for_ip(
            databaseinfra=self.infra,
            ip=self.instance.address
        )

        self.instance.save()

    def undo(self):
        self.provider.remove_databases_dns_for_ip(
            databaseinfra=self.infra,
            ip=self.instance.address
        )


class RegisterDNSVip(DNSStep):

    def __unicode__(self):
        return "Registry dns for VIP..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    @property
    def vip(self):
        return Vip.objects.get(databaseinfra=self.infra)

    def do(self):
        if not self.is_valid:
            return

        self.provider.create_database_dns_for_ip(
            databaseinfra=self.infra,
            ip=self.vip.vip_ip
        )

    def undo(self):
        if self.is_valid:
            return

        self.provider.remove_databases_dns_for_ip(
            databaseinfra=self.infra,
            ip=self.vip.vip_ip
        )


class CreateDNSSentinel(CreateDNS):

    @property
    def database_sufix(self):
        base = super(CreateDNSSentinel, self).database_sufix
        if not self.instance.is_database:
            base['database_sufix'] = 'sentinel'
        return base


class CheckIsReady(DNSStep):

    def __unicode__(self):
        return "Waiting for DNS..."

    def do(self):
        if self.instance.id != self.infra.instances.first().id:
            return

        check_dns = self.credentials.get_parameter_by_name('check_dns')
        if str(check_dns).lower() != 'true':
            return

        for dns in DatabaseInfraDNSList.objects.filter(
            databaseinfra=self.infra.id
        ):
            if not check_nslookup(dns.dns, self.credentials.project):
                raise EnvironmentError("DNS {} is not ready".format(dns.dns))
