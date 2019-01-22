from dbaas_networkapi.models import Vip as NetworkApiVip
from physical.models import Vip, Environment
from bson import ObjectId, json_util
import json
import requests
from dbaas_credentials.models import CredentialType
from util import get_credentials_for



class MigrateVip(object):

    def __init__(self):
        self._credential = None

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                Environment.objects.get(name='prod'), CredentialType.VIP_PROVIDER
            )

        return self._credential

    @property
    def networkapi_vips(self):
        return NetworkApiVip.objects.all()


    @staticmethod
    def to_mongo(networkapi_vip):
        try:
            physical_vip = Vip.objects.get(infra=networkapi_vip.databaseinfra)
        except Vip.DoesNotExist:
            physical_vip = None

        mongo_dict = {
            "_id": {"$oid": physical_vip.identifier if physical_vip else ObjectId()},
            "port": 3306,
            "group": networkapi_vip.databaseinfra.name,
            "vip_ip": networkapi_vip.vip_ip,
            "vip_id": networkapi_vip.vip_id,
            "pool_id": networkapi_vip.pool_id,
            "dscp": networkapi_vip.dscp
        }

        return mongo_dict

    @staticmethod
    def to_json(mongo_dict):
        return json.dumps(mongo_dict, default=json_util.default)

    def do(self):
        for vip in self.networkapi_vips:
            mongo_dict = self.to_mongo(vip)
            Vip.objects.get_or_create(
                infra=vip.databaseinfra,
                identifier=mongo_dict['_id']["$oid"]
            )
            print(self.to_json(mongo_dict))

    def validate(self):
        for networkapi_vip in self.networkapi_vips:
            physical_vip = Vip.objects.get(infra=networkapi_vip.databaseinfra)
            resp = requests.get("{}/networkapi/{}/vip/{}".format(
                self.credential.endpoint,
                physical_vip.infra.environment.name,
                physical_vip.identifier)
            )
            if resp.ok:
                resp = resp.json()
                assert 3306 == resp['port']
                assert networkapi_vip.vip_ip == resp['vip_ip']
                assert networkapi_vip.vip_id == resp['vip_id']
                assert networkapi_vip.pool_id == resp['pool_id']
                assert networkapi_vip.dscp == resp['dscp']
                assert networkapi_vip.databaseinfra.name == resp['group']
