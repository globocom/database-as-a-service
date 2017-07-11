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
