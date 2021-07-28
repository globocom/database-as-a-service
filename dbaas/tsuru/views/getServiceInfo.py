from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from logical.models import Database
from rest_framework.response import Response
from utils import get_url_env, get_database, LOG


class GetServiceInfo(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    def get(self, request, database_name, format=None):
        env = get_url_env(request)
        try:
            database = get_database(database_name, env)
            info = {'used_size_in_bytes': str(database.used_size_in_bytes)}
        except IndexError as e:
            info = {}
            LOG.warn(
                "There is not a database {} on {}. {}".format(
                    database_name, env, e
                )
            )

        LOG.info("Info = {}".format(info))

        return Response(info)
