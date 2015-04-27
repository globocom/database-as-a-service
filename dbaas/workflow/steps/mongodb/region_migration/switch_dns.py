# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_dnsapi.provider import DNSAPIProvider
from physical.models import Instance
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class SwitchDNS(BaseStep):

    def __unicode__(self):
        return "Switching DNS..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']

            source_instances = []
            source_hosts = []
            for instance in Instance.objects.filter(databaseinfra=databaseinfra):
                if not instance.future_instance:
                    continue
                source_instances.append(instance)
                if instance.instance_type != instance.REDIS_SENTINEL:
                    source_hosts.append(instance.hostname)
            workflow_dict['source_instances'] = source_instances
            workflow_dict['source_hosts'] = source_hosts

            workflow_dict['dns_changed_hosts'] = []
            workflow_dict['dns_changed_instances'] = []

            for source_host in source_hosts:
                old_ip = source_host.address
                hostname = source_host.hostname
                source_host.hostname = old_ip

                target_host = source_host.future_host
                new_ip = target_host.address
                target_host.hostname = hostname

                LOG.info("Calling dnsapi update dns hosts...")
                DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                           dns=hostname,
                                                           old_ip=old_ip,
                                                           new_ip=new_ip)

                source_host.save()
                target_host.save()

                workflow_dict['dns_changed_hosts'].append({
                                                          'source_host': source_host,
                                                          'target_host': target_host,
                                                          'hostname': hostname,
                                                          'old_ip': old_ip,
                                                          'new_ip': new_ip})

            for source_instance in source_instances:
                old_ip = source_instance.address
                dns = source_instance.dns
                source_instance.dns = old_ip

                target_instance = source_instance.future_instance
                new_ip = target_instance.address
                target_instance.dns = dns

                LOG.info("Calling dnsapi update dns instances...")
                DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                           dns=dns,
                                                           old_ip=old_ip,
                                                           new_ip=new_ip)

                source_instance.save()
                target_instance.save()

                workflow_dict['dns_changed_instances'].append({
                                                              'source_instance': source_instance,
                                                              'target_instance': target_instance,
                                                              'dns': dns,
                                                              'old_ip': old_ip,
                                                              'new_ip': new_ip})

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            databaseinfra = workflow_dict['databaseinfra']

            if 'dns_changed_hosts' in workflow_dict:
                for dns_changed_host in workflow_dict['dns_changed_hosts']:
                    source_host = dns_changed_host['source_host']
                    target_host = dns_changed_host['target_host']
                    new_ip = dns_changed_host['new_ip']
                    old_ip = dns_changed_host['old_ip']
                    hostname = dns_changed_host['hostname']
                    target_host.hostname = new_ip
                    target_host.save()
                    source_host.hostname = hostname
                    source_host.save()
                    DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                               dns=hostname,
                                                               old_ip=new_ip,
                                                               new_ip=old_ip)

                for dns_changed_instance in workflow_dict['dns_changed_instances']:
                    source_instance = dns_changed_instance['source_instance']
                    target_instance = dns_changed_instance['target_instance']
                    new_ip = dns_changed_instance['new_ip']
                    old_ip = dns_changed_instance['old_ip']
                    dns = dns_changed_instance['dns']
                    target_instance.dns = new_ip
                    target_instance.save()
                    source_instance.dns = dns
                    source_instance.save()
                    DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                               dns=dns,
                                                               old_ip=new_ip,
                                                               new_ip=old_ip)

                return True

            for source_host in workflow_dict['source_hosts']:
                target_host = source_host.future_host
                hostname = target_host.hostname
                old_ip = target_host.address
                target_host.hostname = old_ip
                target_host.save()

                new_ip = source_host.address
                source_host.hostname = hostname
                source_host.save()

                LOG.info("Calling dnsapi update dns hosts...")
                DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                           dns=hostname,
                                                           old_ip=old_ip,
                                                           new_ip=new_ip)

            for source_instance in workflow_dict['source_instances']:
                target_instance = source_instance.future_instance
                dns = target_instance.dns
                old_ip = target_instance.address
                target_instance.dns = old_ip
                target_instance.save()

                new_ip = source_instance.address
                source_instance.dns = dns
                source_instance.save()

                LOG.info("Calling dnsapi update dns instances...")
                DNSAPIProvider.update_database_dns_content(databaseinfra=databaseinfra,
                                                           dns=dns,
                                                           old_ip=old_ip,
                                                           new_ip=new_ip)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
