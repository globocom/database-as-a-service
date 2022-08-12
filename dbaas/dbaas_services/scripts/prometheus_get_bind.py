import json
import requests
from dbaas.logical.models import Database


class InsertBind(object):

    def prometheus(self):
        db = Database
        databases = db.objects.all()

        for database in databases:
            data_query = "query=tsuru_service_instance_bind{service_instance="
            query = "'{}'".format(database)
            data_query = data_query + query + "}"
            response = requests.get("https://prometheus-br1.tsuru.gcp.i.globo/api/v1/query", params=data_query,
                                    verify=False)
            print(response.url)
            try:
                content = json.loads(response.content)
                metric = content["data"]["result"][0]["metric"]
                if metric:
                    databese_objects = db.objects.get(id=database.id)
                    if databese_objects:
                        if databese_objects.apps_bind_name:
                            databese_objects.apps_bind_name += ', ' + metric["app"]
                        else:
                            databese_objects.apps_bind_name = metric["app"]
                        databese_objects.save()
                    print(content)
            except Exception as e:
                print(e)
                pass


a = InsertBind()
print(a.prometheus())
