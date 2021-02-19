from __future__ import print_function
import requests
import logging
import copy
from time import sleep
from dbaas_credentials.models import CredentialType
from util import get_credentials_for


LOG = logging.getLogger(__name__)


class RunJobError(Exception):
    pass


class GetJobError(Exception):
    pass


class WaitJobTimeoutError(Exception):
    pass


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
        >>> cli.create_acl()
        Here we add 2 acls:
            - source: 1.1.1.1/27 destination: 9.9.9.9/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 9.9.9.9/20 tcp port: 27017

        Ex. U can pass sources with specific port.
        >>> from util.aclapi import AddACLAccess
        >>> sources = [("1.1.1.1/27", 22), ("2.2.2.2/27", 443)]
        >>> destinations = ["9.9.9.9/20"]
        >>> cli = AddACLAccess(env, sources, destinations)
        >>> cli.create_acl()
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
        >>> cli.create_acl()
        Here we add 4 acls:
            - source: 1.1.1.1/27 destination: 10.10.10.10/20 tcp port: 27017
            - source: 1.1.1.1/27 destination: 11.11.11.11/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 10.10.10.10/20 tcp port: 27017
            - source: 2.2.2.2/27 destination: 11.11.11.11/20 tcp port: 27017

        Ex. If the specific port and default port not setted, we create acl
        with ip EACH source
        >>> from util.aclapi import AddACLAccess
        >>> sources = ["1.1.1.1/27", "2.2.2.2/27"]
        >>> destinations = ["10.10.10.10/20", "11.11.11.11/20"]
        >>> cli = AddACLAccess(env, sources, destinations)
        >>> cli.create_acl()
        Here we add 4 acls:
            - source: 1.1.1.1/27 destination: 10.10.10.10/20 ip
            - source: 1.1.1.1/27 destination: 11.11.11.11/20 ip
            - source: 2.2.2.2/27 destination: 10.10.10.10/20 ip
            - source: 2.2.2.2/27 destination: 11.11.11.11/20 ip

        Ex. U can do between networks
        >>> from util.aclapi import AddACLAccess
        >>> networks = ["1.1.1.1/27", "2.2.2.2/27", "10.10.10.10/20"]
        >>> cli = AddACLAccess(env, networks=networks)
        >>> cli.execute_between_networks()
        Here we add 4 acls:
            - source: 1.1.1.1/27 destination: 2.2.2.2/27 ip
            - source: 1.1.1.1/27 destination: 10.10.10.10/20 ip
            - source: 2.2.2.2/27 destination: 1.1.1.1/27 ip
            - source: 2.2.2.2/27 destination: 10.10.10.10/20 ip
            - source: 10.10.10.10/20 destination: 1.1.1.1/27 ip
            - source: 10.10.10.10/20 destination: 2.2.2.2/27 ip
    """

    wait_job_attemps = 60
    wait_job_timeout = 10

    def __init__(self, env, sources=None, destinations=None,
                 default_port=None, description=None, networks=None):
        self.env = env
        self.sources = sources
        self.destinations = destinations
        self.networks = networks
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

    def _make_acl_url(self, source):
        return '{}api/ipv4/acl/{}'.format(
            self.credential.endpoint,
            source
        )

    def _make_run_job_url(self, job_id):
        return '{}/run'.format(
            self._make_get_job_url(job_id)
        )

    def _make_get_job_url(self, job_id):
        return '{}api/jobs/{}'.format(
            self.credential.endpoint,
            job_id
        )

    def _wait_job_finish(self, job_id):
        attemps = copy.copy(self.wait_job_attemps)
        while attemps > 0:
            job = self._get_job(job_id)
            if job.get('jobs', {}).get('status') == 'SUCCESS':
                LOG.info("Job {} executed with SUCCESS!!".format(
                    job_id
                ))
                return
            sleep(self.wait_job_timeout)
            attemps -= 1
        err_msg = "Job not finished after {} attemps. JOB: {}!!".format(
            self.wait_job_attemps, job
        )
        LOG.error(err_msg)
        raise WaitJobTimeoutError(err_msg)

    def _create_acl(self, source, port, execute_job=True):
        payload = self._make_payload(source, port)
        resp = requests.put(
            self._make_acl_url(source),
            json=payload,
            auth=(self.credential.user, self.credential.password),
            verify=False
        )
        if resp.ok:
            LOG.info("ACL {} created with SUCCESS!!".format(payload))
            if execute_job:
                jobs = set(resp.json().get('jobs', []))
                for job_id in jobs:
                    resp = self._run_job(job_id)
        else:
            err_msg = "FAIL for payload: {} Status: {} Error: {}!!".format(
                payload, resp.status_code, resp.content
            )
            LOG.error(err_msg)
            raise Exception(err_msg)

    def _get_job(self, job_id):
        resp = requests.get(
            self._make_get_job_url(job_id),
            auth=(self.credential.user, self.credential.password),
            timeout=110,
            verify=False
        )
        if resp.ok:
            LOG.info("Get Job {} executed with SUCCESS!!".format(
                job_id
            ))
            return resp.json()
        else:
            err_msg = "FAIL to get job: {} Status: {} Error: {}!!".format(
                job_id, resp.status_code, resp.content
            )
            LOG.error(err_msg)
            raise GetJobError(err_msg)

    def _run_job(self, job_id):
        try:
            resp = requests.get(
                self._make_run_job_url(job_id),
                auth=(self.credential.user, self.credential.password),
                timeout=110,
                verify=False
            )
        except requests.Timeout:
            return self._wait_job_finish(job_id)
        if resp.ok:
            LOG.info("Job {} executed with SUCCESS!!".format(
                job_id
            ))
        else:
            err_msg = "FAIL for job: {} Status: {} Error: {}!!".format(
                job_id, resp.status_code, resp.content
            )
            LOG.error(err_msg)
            raise RunJobError(err_msg)

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
                msg += ' port: {}'.format(
                    rule['l4-options']['dest-port-start']
                )
            msg += '\n'
            rules.append(rule)
        LOG.info(msg)

        return {
            "kind": "object#acl",
            "rules": rules
        }

    def _parse_source(self, source):
        port = None
        if isinstance(source, tuple):
            source, port = source
        return source, port

    def create_acl(self, execute_job=True):
        for source in self.sources:
            source, port = self._parse_source(source)
            LOG.info("Creating ACL for source: {}".format(source))
            LOG.info("Sending PUT to ACLAPI...")
            self._create_acl(source, port, execute_job=execute_job)

    def create_acl_between_networks(self, execute_job=True):
        for source in self.networks:
            destination = copy.copy(self.networks)
            destination.remove(source)
            self.sources = [source]
            self.destinations = destination
            self.create_acl(execute_job=execute_job)
