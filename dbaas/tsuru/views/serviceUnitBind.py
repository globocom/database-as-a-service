from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.response import Response
from logical.models import Database
from rest_framework import status
from ..utils import check_maintenance


class ServiceUnitBind(APIView):
    renderer_classes = (JSONRenderer, JSONPRenderer)
    model = Database

    @check_maintenance
    def post(self, request, database_name, format=None):
        return Response(None, status.HTTP_201_CREATED)

    @check_maintenance
    def delete(self, request, database_name, format=None):
        return Response(status.HTTP_204_NO_CONTENT)