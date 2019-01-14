from dbaas_networkapi.models import Vip as NetworkApiVip
from physical.models import Vip
from bson import ObjectId, json_util
import json



class MigrateVip(object):
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
