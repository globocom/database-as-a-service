from dbaas_dnsapi.provider import DNSAPIProvider
from base import BaseInstanceStep


class DNSStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DNSStep, self).__init__(instance)
        self.provider = DNSAPIProvider

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

    def __unicode__(self):
        return "Changing DNS endpoint..."

    def do(self):
        old_instance = self.instance.future_instance
        DNSAPIProvider.update_database_dns_content(
            self.infra, old_instance.dns,
            old_instance.address, self.instance.address
        )

        self.instance.dns = old_instance.dns
        self.instance.save()

        old_instance.dns = old_instance.address
        old_instance.save()

        self.host.hostname = self.instance.dns
        self.host.save()

        old_host = self.host.future_host
        old_host.hostname = old_instance.address
        old_host.save()
