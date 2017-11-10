# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_networkapi.provider import NetworkProvider
from dbaas_networkapi.equipment import Equipment
from dbaas_networkapi.dbaas_api import DatabaseAsAServiceApi
from dbaas_networkapi.utils import get_vip_ip_from_databaseinfra
from dbaas_dnsapi.utils import get_dns_name_domain
from dbaas_dnsapi.models import FOXHA
from dbaas_cloudstack.models import HostAttr
from django.core.exceptions import ObjectDoesNotExist
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0024

LOG = logging.getLogger(__name__)


class CreateVip(BaseStep):

    def __unicode__(self):
        return "Creating VIP..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            dbaas_api = DatabaseAsAServiceApi(databaseinfra=databaseinfra)
            equipments = []

            for instance in workflow_dict['instances']:
                host = instance.hostname
                host_attr = HostAttr.objects.get(host=host)
                equipments.append(Equipment(
                                  name='{}-{}'.format(dbaas_api.vm_name, host_attr.vm_id),
                                  ip=host.address,
                                  port=instance.port))

            LOG.info("Creating VIP to equipments = [{}]".format(equipments))
            networkprovider = NetworkProvider(dbaas_api=dbaas_api)

            vipname, vipdomain = get_dns_name_domain(databaseinfra=databaseinfra,
                                                     name=databaseinfra.name,
                                                     type=FOXHA)
            vip_dns = '%s.%s' % (vipname, vipdomain)
            LOG.info("VIP dns = {}".format(vip_dns))
            vip = networkprovider.create_vip(equipments=equipments,
                                             port=3306,
                                             vip_dns=vip_dns)

            LOG.info("VIP created: {}".format(vip))

            LOG.info("Updating databaseinfra endpoint...")

            databaseinfra.endpoint = "{}:{}".format(vip.vip_ip, 3306)
            databaseinfra.save()

            workflow_dict['vip'] = vip

            workflow_dict['databaseinfra'] = databaseinfra

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0024)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            if 'databaseinfra' not in workflow_dict and 'hosts' not in workflow_dict:
                LOG.info(
                    "We could not find a databaseinfra inside the workflow_dict")
                return False

            databaseinfra = workflow_dict['databaseinfra']
            try:
                vip_ip = get_vip_ip_from_databaseinfra(databaseinfra=databaseinfra)
            except ObjectDoesNotExist:
                return True

            LOG.info("Deleting VIP {}".format(vip_ip))
            dbaas_api = DatabaseAsAServiceApi(databaseinfra=databaseinfra)
            networkprovider = NetworkProvider(dbaas_api=dbaas_api)
            networkprovider.delete_vip(vip_ip=vip_ip)
            LOG.info("VIP deleted")

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0024)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
