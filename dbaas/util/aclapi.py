from __future__ import print_function
import requests
from dbaas_credentials.models import CredentialType
from util import get_credentials_for


class AddACLAccess(object):
    """
        Class to add ACL's on ACLAPI
        This client only create acls, do not execute the jobs.

        Ex. U can pass sources with default_port. We add the default port
        too all sources
        >>> from util.aclapi import AddACLAccess
        >>> sources = ["1.1.1.1/27", "2.2.2.2/27"]
        >>> destinations = ["9.9.9.9/20"]
        >>> default_port = 27017
        >>> cli = AddACLAccess(env, sources, destinations, default_port)
        >>> cli.execute()
        Here we add 2 acls:
            - source: 1.1.1.1/27 destination: 9.9.9.9/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 9.9.9.9/20 tcp port: 27017

        Ex. U can pass sources with specific port.
        >>> from util.aclapi import AddACLAccess
        >>> sources = [("1.1.1.1/27", 22), ("2.2.2.2/27", 443)]
        >>> destinations = ["9.9.9.9/20"]
        >>> cli = AddACLAccess(env, sources, destinations)
        >>> cli.execute()
        Here we add 2 acls:
            - source: 1.1.1.1/27 destination: 9.9.9.9/20 tcp port: 22
            - source: 2.2.2.2/27 destination: 9.9.9.9/20 tcp port: 443

        Ex. U can pass multiple destinations. We create all destination to
        EACH source
        >>> from util.aclapi import AddACLAccess
        >>> sources = ["1.1.1.1/27", "2.2.2.2/27"]
        >>> destinations = ["10.10.10.10/20", "11.11.11.11/20"]
        >>> default_port = 27017
        >>> cli = AddACLAccess(env, sources, destinations, default_port)
        >>> cli.execute()
        Here we add 4 acls:
            - source: 1.1.1.1/27 destination: 10.10.10.10/20 tcp port: 27017
            - source: 1.1.1.1/27 destination: 11.11.11.11/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 10.10.10.10/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 11.11.11.11/20 tcp port: 27017

        Ex. If the specific port and default port not setted, we create acl with ip
        EACH source
        >>> from util.aclapi import AddACLAccess
        >>> sources = ["1.1.1.1/27", "2.2.2.2/27"]
        >>> destinations = ["10.10.10.10/20", "11.11.11.11/20"]
        >>> cli = AddACLAccess(env, sources, destinations)
        >>> cli.execute()
        Here we add 4 acls:
            - source: 1.1.1.1/27 destination: 10.10.10.10/20 ip
            - source: 1.1.1.1/27 destination: 11.11.11.11/20 ip
            - source: 2.2.2.2/27 destination: 10.10.10.10/20 ip
            - source: 2.2.2.2/27 destination: 11.11.11.11/20 ip
    """
    def __init__(self, env, sources, destinations, default_port=None, description=None):
        self.env = env
        self.sources = sources
        self.destinations = destinations
        self.default_port = default_port
        self._credential = None
        self.description = description

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                environment=self.env,
                credential_type=CredentialType.ACLAPI)
        return self._credential

    def _make_url(self, source):
        return '{}api/ipv4/acl/{}'.format(
            self.credential.endpoint,
            source
        )

    def _request(self, source, payload):
        resp = requests.put(
            self._make_url(source),
            json=payload,
            auth=(self.credential.user, self.credential.password)
        )

        return resp

    def _make_payload(self, source, port=None):
        rules = []
        msg = 'destinations:\n'
        for destination in self.destinations:
            rule = {
                "action": "permit",
                "protocol": "tcp" if port or self.default_port else "ip",
                "source": source,
                "destination": destination,
            }
            if self.description:
                rule['description'] = self.description
            msg += '{destination} {protocol}'.format(**rule)
            if self.default_port:
                rule["l4-options"] = {
                    "dest-port-op": "eq",
                    "dest-port-start": str(port or self.default_port)
                }
                msg += ' port: {}'.format(rule['l4-options']['dest-port-start'])
            msg += '\n'
            rules.append(rule)
        print(msg)

        return {
            "kind": "object#acl",
            "rules": rules
        }

    def _parse_source(self, source):
        port = None
        if isinstance(source, tuple):
            source, port = source
        return source, port

    def execute(self):
        for source in self.sources:
            source, port = self._parse_source(source)
            print("Creating ACL for source: {}".format(source))
            payload = self._make_payload(source, port)
            print("Sending PUT to ACLAPI...")
            resp = self._request(source, payload)
            if resp.ok:
                print("SUCCESS!!\n\n\n")
            else:
                print("FAIL Status: {} Error: {}!!\n\n\n".format(resp.status_code, resp.content))
