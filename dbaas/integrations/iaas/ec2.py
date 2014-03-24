# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from urlparse import urlparse
import boto.ec2.regioninfo
import boto.ec2.connection
from django.db import transaction
from django.conf import settings
from physical import models
from drivers import factory_for
import time
#import timeout_decorator


LOG = logging.getLogger(__name__)

def get_ec2_api():
    # if you want to setup proxy and other custom configurations, see http://boto.readthedocs.org/en/latest/boto_config_tut.html
    if getattr(settings, 'EC2_URL', None):
        url = urlparse(settings.EC2_URL)

        region = boto.ec2.regioninfo.RegionInfo(None, 'custom', url.hostname)
        conn = boto.ec2.connection.EC2Connection(
            aws_access_key_id=settings.EC2_ACCESS_KEY,
            aws_secret_access_key=settings.EC2_SECRET_KEY,
            host=url.hostname,
            path=url.path,
            region=region,
            port=url.port)
    else:
        conn = boto.ec2.connect_to_region(
            getattr(settings, "EC2_REGION", None),
            aws_access_key_id=settings.EC2_ACCESS_KEY,
            aws_secret_access_key=settings.EC2_SECRET_KEY)
        assert conn is not None, "EC2_REGION is invalid. Valid values are: %s" % \
            ', '.join([ r.name for r in boto.ec2.regions() ])
    return conn


class Ec2Provider(object):

    #@timeout_decorator.timeout(60)
    @transaction.commit_on_success
    def create_instance(self, databaseinfra):
        ec2_api = get_ec2_api()
        reservation = ec2_api.run_instances(settings.EC2_AMI_ID, subnet_id=settings.EC2_SUBNET_ID)
        i = reservation.instances[0]

        # due to a bug in boto, I put this call to allow get instance.ip_address
        while not i.ip_address:
            LOG.debug('Refresh instances status')
            time.sleep(1)
            i.update()

        LOG.info("Created instance %s", i.ip_address)
        host = models.Host()
        host.hostname = i.public_dns_name
        host.save()
        instance = models.Instance()
        instance.address = i.ip_address
        # instance.address = i.public_dns_name
        # instance.address = i.dns_name
        instance.port = factory_for(databaseinfra).default_port
        instance.databaseinfra = databaseinfra
        instance.is_active = False
        instance.is_arbiter = False
        instance.hostname = host
        instance.save()
        return instance

# >>> pprint(i.__dict__)
# {'_in_monitoring_element': False,
#  '_placement': globoi.com,
#  '_previous_state': None,
#  '_state': stopped(80),
#  'ami_launch_index': u'0',
#  'architecture': u'x86_64',
#  'block_device_mapping': None,
#  'client_token': '',
#  'connection': EC2Connection:orquestra.qa01.globoi.com,
#  'dns_name': u'qhlabvld123.globoi.com',
#  'eventsSet': None,
#  'group_name': None,
#  'groups': [],
#  'hypervisor': None,
#  'id': u'i-00001789',
#  'image_id': u'ami-00000042',
#  'databaseinfra_profile': None,
#  'databaseinfra_type': u'large',
#  'interfaces': [],
#  'ip_address': u'10.248.46.183',
#  'item': '',
#  'kernel': None,
#  'key_name': None,
#  'launch_time': u'2013-10-10T18:47:01.066369Z',
#  'monitored': False,
#  'monitoring': '',
#  'monitoring_state': u'disabled',
#  'persistent': False,
#  'platform': '',
#  'private_dns_name': None,
#  'private_ip_address': '',
#  'product_codes': [],
#  'public_dns_name': u'qhlabvld123.globoi.com',
#  'ramdisk': None,
#  'reason': '',
#  'region': RegionInfo:orquestra,
#  'requester_id': None,
#  'root_device_name': u'/dev/xvda1',
#  'root_device_type': u'nfs',
#  'sourceDestCheck': u'true',
#  'spot_databaseinfra_request_id': None,
#  'state_reason': None,
#  'subnet_id': u'subnet-00001145',
#  'tags': {},
#  'virtualization_type': u'paravirt',
#  'vpc_id': u'vpc-00061030'}

