from dbaas_credentials.models import CredentialType
from dbaas_dnsapi.models import HOST, INSTANCE, FOXHA, DatabaseInfraDNSList
from dbaas_dnsapi.provider import DNSAPIProvider
from dbaas_dnsapi.utils import add_dns_record
from util import get_credentials_for, check_dns
from base import BaseInstanceStep
import socket


class DNSStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DNSStep, self).__init__(instance)
        self.provider = DNSAPIProvider
        self._vip = None

    def is_ipv4(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

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



class ChangeVipEndpoint(DNSStep):

    def __unicode__(self):
        return "Changing VIP DNS endpoint..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return

        self.infra.endpoint = self.infra.endpoint.replace(
            self.vip.vip_ip, self.future_vip.vip_ip
        )
        self.infra.save()

    def undo(self):
        raise Exception("This step doesnt have rollback")


class CreateDNS(DNSStep):

    def __unicode__(self):
        return "Creating DNS..."

    def do(self):
        if self.host.hostname == self.host.address:
            self.host.hostname = add_dns_record(
                databaseinfra=self.infra,
                name=self.instance.vm_name,
                ip=self.host.address,
                type=HOST,
                is_database=self.instance.is_database
            )
            self.host.save()

        self.instance.dns = add_dns_record(
            databaseinfra=self.infra,
            name=self.instance.vm_name,
            ip=self.instance.address,
            type=INSTANCE,
            is_database=self.instance.is_database
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

    def __init__(self, *args, **kw):
        super(RegisterDNSVip, self).__init__(*args, **kw)
        self._infra = None
        self.do_export = True
        self._env = None

    def __unicode__(self):
        return "Registry dns for VIP..."

    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def _do_database_dns_for_ip(self, func):
        if not self.is_valid:
            return
        return func(
            databaseinfra=self._infra or self.infra,
            ip=self.vip.vip_ip,
            do_export=self.do_export,
            env=self._env or self.infra.environment,
            **{'dns_type': 'CNAME'} if not self.is_ipv4(self.vip.vip_ip) else {}
        )

    def do(self):
        self._do_database_dns_for_ip(
            self.provider.create_database_dns_for_ip
        )

    def undo(self):
        self._do_database_dns_for_ip(
            self.provider.remove_databases_dns_for_ip
        )


class RegisterDNSVipMigrate(RegisterDNSVip):
    def __unicode__(self):
        return "Registry dns for VIP of new environment..."

    def do(self):
        if not self.is_valid:
            return
        self.vip = self.future_vip
        self._env = self.environment
        dns = add_dns_record(
            self.infra,
            self.infra.name,
            self.vip.vip_ip,
            FOXHA,
            is_database=False
        )
        assert self.infra.endpoint_dns == "{}:3306".format(dns)
        return super(RegisterDNSVipMigrate, self).do()

    def undo(self):
        raise Exception("This step doesnt have rollback")


class UnregisterDNSVipMigrate(RegisterDNSVip):
    def __unicode__(self):
        return "Unregistry dns for VIP of old environment..."
    def do(self):
        self.do_export = False
        return super(UnregisterDNSVipMigrate, self).undo()

    def undo(self):
        raise Exception("This step doesnt have rollback")


class CheckIsReady(DNSStep):

    def __unicode__(self):
        return "Waiting for DNS..."

    def _check_dns_for(self, dns_to_check, ip_to_check):
        for dns in DatabaseInfraDNSList.objects.filter(
            databaseinfra=self.infra.id,
            dns=dns_to_check
        ):
            if not check_dns(dns.dns, self.credentials.project, ip_to_check=ip_to_check):
                raise EnvironmentError("DNS {} is not ready".format(dns.dns))

    @property
    def must_check(self):
        must_check_dns = self.credentials.get_parameter_by_name('check_dns')
        return str(must_check_dns).lower() == 'true'

    def do(self):
        if not self.must_check:
            return

        for instance in self.instance.hostname.instances.all():
            self._check_dns_for(instance.dns, self.host.address)


class CheckVipIsReady(CheckIsReady):

    def __unicode__(self):
        return "Waiting for VIP DNS..."


    def do(self):
        if not self.must_check:
            return
        self._check_dns_for(self.infra.endpoint_dns.split(":")[0], self.future_vip.vip_ip)
